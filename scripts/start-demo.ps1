$ErrorActionPreference = "Stop"
$Namespace = "ev-fleet"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "       EV FLEET DATA PLATFORM - DEMO START       " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/7] Checking Docker..." -ForegroundColor Yellow
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker Desktop is not running." }
Write-Host "Docker = PASS" -ForegroundColor Green

Write-Host "[2/7] Checking Kubernetes..." -ForegroundColor Yellow
kubectl cluster-info *> $null
if ($LASTEXITCODE -ne 0) { throw "Kubernetes cluster is unavailable." }
Write-Host "Kubernetes = PASS" -ForegroundColor Green

Write-Host "[3/7] Checking namespace..." -ForegroundColor Yellow
kubectl get namespace $Namespace *> $null
if ($LASTEXITCODE -ne 0) { throw "Namespace $Namespace is unavailable." }
Write-Host "Namespace = PASS" -ForegroundColor Green

Write-Host "[4/7] Waiting for application deployments..." -ForegroundColor Yellow
foreach ($Deployment in @("evfleet-backend","evfleet-frontend","evfleet-consumer")) {
    kubectl rollout status deployment/$Deployment -n $Namespace --timeout=120s
    if ($LASTEXITCODE -ne 0) { throw "$Deployment rollout failed." }
    Write-Host "$Deployment = PASS" -ForegroundColor Green
}

Write-Host "[5/7] Checking platform services..." -ForegroundColor Yellow
foreach ($Service in @("evfleet-backend","evfleet-frontend","evfleet-kafka","evfleet-postgres")) {
    kubectl get service $Service -n $Namespace *> $null
    if ($LASTEXITCODE -ne 0) { throw "Service $Service is unavailable." }
    Write-Host "$Service = PASS" -ForegroundColor Green
}

Write-Host "[6/7] Checking backend, frontend and real-world AI..." -ForegroundColor Yellow

$BackendPod = kubectl get pods -n $Namespace -l app=evfleet-backend -o jsonpath='{.items[0].metadata.name}'
if ([string]::IsNullOrWhiteSpace($BackendPod)) { throw "Backend pod unavailable." }

kubectl exec -n $Namespace $BackendPod -- curl -fsS http://127.0.0.1:8000/ *> $null
if ($LASTEXITCODE -ne 0) { throw "Backend health check failed." }
Write-Host "Backend health = PASS" -ForegroundColor Green

$FrontendPod = kubectl get pods -n $Namespace -l app=evfleet-frontend -o jsonpath='{.items[0].metadata.name}'
if ([string]::IsNullOrWhiteSpace($FrontendPod)) { throw "Frontend pod unavailable." }

kubectl exec -n $Namespace $FrontendPod -- curl -fsS http://127.0.0.1/health *> $null
if ($LASTEXITCODE -ne 0) { throw "Frontend health check failed." }
Write-Host "Frontend health = PASS" -ForegroundColor Green

kubectl exec -n $Namespace $BackendPod -- python -c "import os; p='/app/backend/models/real_world_ev_anomaly_isolation_forest.joblib'; assert os.path.exists(p); print('Real-world model = PASS')" 
if ($LASTEXITCODE -ne 0) { throw "Real-world AI model unavailable." }

kubectl exec -n $Namespace $BackendPod -- python -c "import urllib.request,json; d=json.dumps({'battery_soc':80.0,'battery_voltage':400.0,'speed':50.0,'battery_temp':30.0}).encode(); r=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/ai/real-world/risk',data=d,headers={'Content-Type':'application/json'},method='POST'),timeout=60); print('AI_HTTP=',r.status); print('AI_RESPONSE=',r.read().decode())"
if ($LASTEXITCODE -ne 0) { throw "Real-world AI inference failed." }
Write-Host "Real-world AI = PASS" -ForegroundColor Green

Write-Host "[7/7] Demo environment ready." -ForegroundColor Yellow

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "              DEMO READY - PASS                  " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend service : evfleet-frontend"
Write-Host "Backend service  : evfleet-backend"
Write-Host "Kafka service    : evfleet-kafka"
Write-Host "PostgreSQL       : evfleet-postgres"
Write-Host "Namespace        : ev-fleet"
Write-Host ""
Write-Host "Project 01 demo environment is READY." -ForegroundColor Green
Write-Host ""
