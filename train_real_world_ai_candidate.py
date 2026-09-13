import duckdb
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score
from datetime import datetime, timezone
import hashlib
import json
import os

src="/features/real_world_ai_dataset.parquet"
model_dir="/models"
os.makedirs(model_dir,exist_ok=True)

con=duckdb.connect()

rows=con.execute(f"""
SELECT
    vehicle_id,
    window_start,
    battery_soc,
    battery_voltage,
    speed,
    battery_temp
FROM read_parquet('{src}')
ORDER BY vehicle_id, window_start
""").fetchall()

con.close()

features=["battery_soc","battery_voltage","speed","battery_temp"]

X=np.array([[r[2],r[3],r[4],r[5]] for r in rows],dtype=float)

split=int(len(X)*0.8)
X_train=X[:split]
X_test=X[split:]

model=IsolationForest(
    n_estimators=300,
    contamination="auto",
    random_state=42,
    n_jobs=-1
)

model.fit(X_train)

normal_pred=model.predict(X_test)

# Controlled abnormal cases derived from real-world feature distributions.
rng=np.random.default_rng(42)
abnormal=X_test.copy()

if len(abnormal)>0:
    abnormal[:,0]=np.clip(abnormal[:,0]*0.45,0,100)
    abnormal[:,1]=abnormal[:,1]*1.30
    abnormal[:,2]=np.clip(abnormal[:,2]*1.80,0,300)
    abnormal[:,3]=abnormal[:,3]+35

y_true=np.concatenate([
    np.zeros(len(X_test),dtype=int),
    np.ones(len(abnormal),dtype=int)
])

pred_normal=(normal_pred==-1).astype(int)
pred_abnormal=(model.predict(abnormal)==-1).astype(int)

y_pred=np.concatenate([pred_normal,pred_abnormal])

precision=precision_score(y_true,y_pred,zero_division=0)
recall=recall_score(y_true,y_pred,zero_division=0)
f1=f1_score(y_true,y_pred,zero_division=0)

model_path=os.path.join(model_dir,"real_world_ev_anomaly_isolation_forest.joblib")
joblib.dump(model,model_path)

with open(model_path,"rb") as f:
    sha=hashlib.sha256(f.read()).hexdigest()

metadata={
    "dataset":"TUMFTM/electric-vehicle-uds-dataset",
    "algorithm":"IsolationForest",
    "model_version":"real-world-1.0.0",
    "trained_at":datetime.now(timezone.utc).isoformat(),
    "training_rows":len(X_train),
    "evaluation_rows":len(X_test),
    "features":features,
    "feature_count":len(features),
    "n_estimators":300,
    "random_state":42,
    "synthetic_abnormal_evaluation_rows":len(abnormal),
    "synthetic_abnormal_precision":float(precision),
    "synthetic_abnormal_recall":float(recall),
    "synthetic_abnormal_f1":float(f1),
    "artifact_path":model_path,
    "artifact_size_bytes":os.path.getsize(model_path),
    "artifact_sha256":sha
}

with open(os.path.join(model_dir,"real_world_model_metadata.json"),"w",encoding="utf-8") as f:
    json.dump(metadata,f,indent=2)

print("REAL_WORLD_ROWS =",len(X))
print("TRAIN_ROWS =",len(X_train))
print("EVALUATION_ROWS =",len(X_test))
print("FEATURES =",features)
print("MODEL_PATH =",model_path)
print("PRECISION =",round(precision,4))
print("RECALL =",round(recall,4))
print("F1 =",round(f1,4))
print("ARTIFACT_SHA256 =",sha)
print("REAL_WORLD_AI_TRAINING = COMPLETE")
