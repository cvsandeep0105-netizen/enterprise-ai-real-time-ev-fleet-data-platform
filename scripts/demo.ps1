$ErrorActionPreference="Stop"
$N="ev-fleet";$BackendPort=18000;$FrontendPort=18080;$BackendForward=$null;$FrontendForward=$null
function S($n,$t){Write-Host "`n==================================================" -ForegroundColor Cyan;Write-Host "[$n/6] $t" -ForegroundColor Cyan;Write-Host "==================================================" -ForegroundColor Cyan}
function P($t){Write-Host "  [PASS] $t" -ForegroundColor Green}
try{
S 1 "Platform & Architecture"
kubectl get namespace $N *> $null;if($LASTEXITCODE-ne 0){throw "Namespace unavailable"}
P "Kubernetes namespace: $N"
foreach($d in "evfleet-backend","evfleet-frontend","evfleet-consumer"){kubectl rollout status deployment/$d -n $N --timeout=120s *> $null;if($LASTEXITCODE-ne 0){throw "$d is not ready"};P "$d is ready"}
Write-Host "  EV telemetry -> Kafka -> Consumer/Processing -> PostgreSQL"
Write-Host "  PostgreSQL -> FastAPI -> React/Vite frontend"
Write-Host "  Real-world EV telemetry -> ML feature vector -> IsolationForest inference"

S 2 "Live Service Health"
foreach($s in "evfleet-backend","evfleet-frontend","evfleet-kafka","evfleet-postgres"){kubectl get service $s -n $N *> $null;if($LASTEXITCODE-ne 0){throw "$s unavailable"};P "$s service exists"}
$BackendPod=kubectl get pods -n $N -l app=evfleet-backend -o jsonpath='{.items[0].metadata.name}'
$FrontendPod=kubectl get pods -n $N -l app=evfleet-frontend -o jsonpath='{.items[0].metadata.name}'
if([string]::IsNullOrWhiteSpace($BackendPod)){throw "Backend pod unavailable"}
if([string]::IsNullOrWhiteSpace($FrontendPod)){throw "Frontend pod unavailable"}
kubectl exec -n $N $BackendPod -- curl -fsS http://127.0.0.1:8000/ *> $null;if($LASTEXITCODE-ne 0){throw "Backend health failed"};P "Backend API health: HTTP 200"
kubectl exec -n $N $FrontendPod -- curl -fsS http://127.0.0.1/health *> $null;if($LASTEXITCODE-ne 0){throw "Frontend health failed"};P "Frontend health: HTTP 200"

S 3 "Open the Live Product"
$BackendForward=Start-Process kubectl -ArgumentList "port-forward","service/evfleet-backend","${BackendPort}:8000","-n",$N -WindowStyle Hidden -PassThru
$FrontendForward=Start-Process kubectl -ArgumentList "port-forward","service/evfleet-frontend","${FrontendPort}:80","-n",$N -WindowStyle Hidden -PassThru
Start-Sleep 3
Invoke-RestMethod "http://127.0.0.1:$BackendPort/"|Out-Null
P "Backend local access: http://127.0.0.1:$BackendPort"
$r=Invoke-WebRequest "http://127.0.0.1:$FrontendPort/health" -UseBasicParsing
if($r.StatusCode-ne 200){throw "Frontend access failed"}
P "Frontend local access: http://127.0.0.1:$FrontendPort"
Start-Process "http://127.0.0.1:$FrontendPort"

S 4 "Real-World AI Demonstration"
$payload=@{battery_soc=80.0;battery_voltage=400.0;speed=50.0;battery_temp=30.0}|ConvertTo-Json
$ai=Invoke-RestMethod "http://127.0.0.1:$BackendPort/ai/real-world/risk" -Method Post -ContentType "application/json" -Body $payload
P "AI inference endpoint: HTTP 200"
Write-Host "  Model source : $($ai.model_source)"
Write-Host "  Model version: $($ai.model_version)"
Write-Host "  Model ID     : $($ai.model_id)"
Write-Host "  Algorithm    : $($ai.algorithm)"
Write-Host "  Anomaly      : $($ai.is_anomaly)"
Write-Host "  Score        : $($ai.anomaly_score)"
Write-Host "  Input        : SOC=$($ai.features.battery_soc)% | Voltage=$($ai.features.battery_voltage)V | Speed=$($ai.features.speed) | Temp=$($ai.features.battery_temp)C"

S 5 "Engineering Evidence"
Write-Host "  Real-world TUMFTM EV UDS dataset"
Write-Host "  Persisted ML artifact + runtime inference"
Write-Host "  FastAPI inference contract"
Write-Host "  Kubernetes + Kafka + PostgreSQL"
Write-Host "  CI/CD + testing + security + observability + scalability"
Write-Host "  Production-oriented local Kubernetes implementation"

S 6 "Interview Demo Complete"
Write-Host "`n  DEMO STATUS: READY" -ForegroundColor Green
Write-Host "  Frontend : http://127.0.0.1:$FrontendPort"
Write-Host "  Backend  : http://127.0.0.1:$BackendPort"
Write-Host "  AI       : POST /ai/real-world/risk"
Write-Host "`n  Browser opened. Use the UI for the walkthrough."
Read-Host "Press ENTER when demo is finished"|Out-Null
}catch{Write-Host "`nDEMO FAILED: $($_.Exception.Message)" -ForegroundColor Red;exit 1}
finally{
if($BackendForward){Stop-Process -Id $BackendForward.Id -Force -ErrorAction SilentlyContinue}
if($FrontendForward){Stop-Process -Id $FrontendForward.Id -Force -ErrorAction SilentlyContinue}
Write-Host "`nTemporary port-forwards closed. Kubernetes workloads were not changed." -ForegroundColor DarkGray
}
