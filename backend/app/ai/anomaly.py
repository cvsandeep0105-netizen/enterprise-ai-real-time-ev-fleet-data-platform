from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

FEATURES = [
    "battery",
    "temp",
    "speed",
]

DEFAULT_MODEL_PATH = Path(
    os.getenv(
        "EV_AI_MODEL_PATH",
        "backend/models/ev_anomaly_isolation_forest.joblib",
    )
)

DEFAULT_MODEL_VERSION = os.getenv(
    "EV_AI_MODEL_VERSION",
    "1.0.0",
)


class EVAnomalyModel:

    def __init__(
        self,
        model_path: str | Path | None = None,
        model_version: str | None = None,
        features: list[str] | None = None,
    ):
        self.model_path = Path(
            model_path
            or os.getenv(
                "EV_AI_MODEL_PATH",
                str(DEFAULT_MODEL_PATH),
            )
        )

        self.model_version = (
            model_version
            or os.getenv(
                "EV_AI_MODEL_VERSION",
                DEFAULT_MODEL_VERSION,
            )
        )

        self.features = list(features or FEATURES)
        self.model = None
        self.metadata: dict = {}

    def _validate_rows(self, rows):
        if len(rows) < 50:
            raise ValueError(
                "At least 50 AI training records are required"
            )

        X = np.asarray(
            [
                [float(row[f]) for f in self.features]
                for row in rows
            ],
            dtype=float,
        )

        if not np.isfinite(X).all():
            raise ValueError(
                "AI training data contains non-finite values"
            )

        return X

    def _validate_artifact(self, artifact):
        if not isinstance(artifact, dict):
            raise ValueError(
                "Invalid AI model artifact"
            )

        if artifact.get("features") != self.features:
            raise ValueError(
                "AI model feature contract mismatch"
            )

        if artifact.get("algorithm") != "IsolationForest":
            raise ValueError(
                "Unsupported AI model algorithm"
            )

        if "model" not in artifact:
            raise ValueError(
                "AI model artifact is missing model"
            )

    def _sha256(self):
        with self.model_path.open("rb") as fh:
            return hashlib.sha256(
                fh.read()
            ).hexdigest()

    def train(self, rows):
        X = self._validate_rows(rows)

        self.model = IsolationForest(
            n_estimators=200,
            contamination="auto",
            random_state=42,
            n_jobs=-1,
        )

        self.model.fit(X)

        trained_at = datetime.now(
            timezone.utc
        ).isoformat()

        model_id = (
            f"ev-anomaly-{uuid.uuid4().hex[:12]}"
        )

        artifact = {
            "model": self.model,
            "features": self.features,
            "algorithm": "IsolationForest",
            "version": 1,
            "model_version": self.model_version,
            "model_id": model_id,
            "trained_at": trained_at,
            "training_rows": len(rows),
            "feature_count": len(self.features),
        }

        self.model_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        joblib.dump(
            artifact,
            self.model_path,
        )

        predictions = self.model.predict(X)

        anomalies = int(
            (predictions == -1).sum()
        )

        artifact_size = (
            self.model_path.stat().st_size
        )

        artifact_sha256 = self._sha256()

        self.metadata = {
            "algorithm": "IsolationForest",
            "model_version": self.model_version,
            "model_id": model_id,
            "trained_at": trained_at,
            "training_rows": len(rows),
            "features": self.features,
            "feature_count": len(self.features),
            "artifact_path": str(
                self.model_path
            ),
            "artifact_size_bytes": artifact_size,
            "artifact_sha256": artifact_sha256,
            "anomalies_detected_in_training": anomalies,
        }

        return self.metadata

    def load(self):
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"AI model artifact not found: "
                f"{self.model_path}"
            )

        artifact = joblib.load(
            self.model_path
        )

        self._validate_artifact(artifact)

        self.model = artifact["model"]

        self.metadata = {
            "algorithm": artifact.get(
                "algorithm",
                "IsolationForest",
            ),
            "model_version": artifact.get(
                "model_version",
                "legacy",
            ),
            "model_id": artifact.get(
                "model_id",
                "legacy",
            ),
            "trained_at": artifact.get(
                "trained_at",
            ),
            "training_rows": artifact.get(
                "training_rows",
            ),
            "features": artifact.get(
                "features",
                self.features,
            ),
            "feature_count": artifact.get(
                "feature_count",
                len(self.features),
            ),
            "artifact_path": str(
                self.model_path
            ),
            "artifact_size_bytes":
                self.model_path.stat().st_size,
            "artifact_sha256":
                self._sha256(),
        }

    def predict(self, row):
        if self.model is None:
            self.load()

        X = np.asarray(
            [[float(row[f]) for f in self.features]],
            dtype=float,
        )

        if not np.isfinite(X).all():
            raise ValueError(
                "AI inference data contains non-finite values"
            )

        prediction = int(
            self.model.predict(X)[0]
        )

        score = float(
            self.model.decision_function(X)[0]
        )

        return {
            "is_anomaly":
                prediction == -1,
            "anomaly_score":
                round(score, 6),
            "algorithm":
                self.metadata.get(
                    "algorithm"
                ),
            "model_version":
                self.metadata.get(
                    "model_version"
                ),
            "model_id":
                self.metadata.get(
                    "model_id"
                ),
            "trained_at":
                self.metadata.get(
                    "trained_at"
                ),
            "features": {
                key: float(row[key])
                for key in self.features
            },
        }

    def status(self):
        if not self.model_path.exists():
            return {
                "enabled": True,
                "artifact_exists": False,
                "model_path":
                    str(self.model_path),
                "configured_model_path":
                    str(self.model_path),
                "configured_model_version":
                    self.model_version,
            }

        self.load()

        return {
            "enabled": True,
            "artifact_exists": True,
            "configured_model_path":
                str(self.model_path),
            "configured_model_version":
                self.model_version,
            **self.metadata,
        }


