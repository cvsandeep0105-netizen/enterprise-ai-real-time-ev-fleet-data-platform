$ErrorActionPreference="Stop"
$N="ev-fleet";$BP=18001;$FP=18081;$bf=$null;$ff=$null
function S($n,$t){Write-Host "`n==================================================" -ForegroundColor Cyan;Write-Host "[$n/10] $t" -ForegroundColor Cyan;Write-Host "==================================================" -ForegroundColor Cyan}
function P($t){Write-Host "  [PASS] $t" -ForegroundColor Green}
function F($t){throw $t}
try{
S 1 "Kubernetes Workloads"
foreach($d in "evfleet-backend","evfleet-frontend","evfleet-consumer"){kubectl -n $N rollout status deployment/$d --timeout=120s *> $null;if($LASTEXITCODE-ne 0){F "$d is not ready"};P "$d ready"}
S 2 "Infrastructure Services"
foreach($s in "evfleet-backend","evfleet-frontend","evfleet-kafka","evfleet-postgres"){kubectl -n $N get service $s *> $null;if($LASTEXITCODE-ne 0){F "$s service unavailable"};P "$s service available"}
S 3 "Backend API"
$bf=Start-Process kubectl -ArgumentList "port-forward","service/evfleet-backend","${BP}:8000","-n",$N -WindowStyle Hidden -PassThru
$ff=Start-Process kubectl -ArgumentList "port-forward","service/evfleet-frontend","${FP}:80","-n",$N -WindowStyle Hidden -PassThru
Start-Sleep 4
$r=Invoke-RestMethod "http://127.0.0.1:$BP/health";if($r.status -ne "HEALTHY"){F "Backend health failed: $($r.status)"};P "Backend /health: HEALTHY"
S 4 "Real Fleet Data"
$v=Invoke-RestMethod "http://127.0.0.1:$BP/vehicles";if($v.Count -ne 7){F "Expected 7 vehicles, got $($v.Count)"};P "Fleet vehicles: 7"
S 5 "Analytics"
$b=Invoke-RestMethod "http://127.0.0.1:$BP/analytics/battery";if($b.Count -ne 7){F "Battery analytics expected 7 vehicles, got $($b.Count)"};P "Battery analytics: 7 vehicles"
$st=Invoke-RestMethod "http://127.0.0.1:$BP/analytics/status";if($st.Count -lt 1){F "Status analytics empty"};P "Vehicle status analytics: valid"
S 6 "Alerts"
$a=Invoke-RestMethod "http://127.0.0.1:$BP/alerts/";if($a.Count -lt 1){F "Alerts endpoint returned no alerts"};P "Alerts endpoint: $($a.Count) real alerts"
$active=@($a|Where-Object{$_.status -eq "ACTIVE"});if($active.Count -lt 1){F "No ACTIVE alert found"};P "Active alerts: $($active.Count)"
S 7 "Frontend API Routing"
$fa=Invoke-RestMethod "http://127.0.0.1:$FP/api/alerts/";if($fa.Count -lt 1){F "Frontend alerts proxy failed"};P "Nginx -> /api/alerts/: HTTP 200"
$fs=Invoke-RestMethod "http://127.0.0.1:$FP/api/dashboard/summary";if($fs.total_vehicles -ne 7){F "Frontend summary invalid"};P "Nginx -> dashboard summary: valid"
S 8 "Live Streaming Advancement"
$v1=Invoke-RestMethod "http://127.0.0.1:$BP/vehicles"
$t1=($v1|ForEach-Object{$_.timestamp}|Sort-Object|Select-Object -Last 1)
Start-Sleep 12
$v2=Invoke-RestMethod "http://127.0.0.1:$BP/vehicles"
$t2=($v2|ForEach-Object{$_.timestamp}|Sort-Object|Select-Object -Last 1)
if([string]$t1 -eq [string]$t2){F "Telemetry timestamp did not advance: $t1"};P "Telemetry advancing: $t1 -> $t2"
S 9 "Real-World AI"
$payload=@{battery_soc=80.0;battery_voltage=400.0;speed=50.0;battery_temp=30.0}|ConvertTo-Json
$ai=Invoke-RestMethod "http://127.0.0.1:$BP/ai/real-world/risk" -Method Post -ContentType "application/json" -Body $payload
if($ai.algorithm -ne "IsolationForest"){F "Unexpected AI algorithm"};if([string]::IsNullOrWhiteSpace($ai.model_id)){F "AI model ID missing"};P "Real-world AI: HTTP 200 / IsolationForest"
S 10 "Product Integrity"
$h=Invoke-WebRequest "http://127.0.0.1:$FP/health" -UseBasicParsing
if($h.StatusCode -ne 200){F "Frontend health failed"};P "Frontend health: HTTP 200"
Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "          FINAL ACCEPTANCE: PASS" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Platform          PASS"
Write-Host "Infrastructure    PASS"
Write-Host "Backend           PASS"
Write-Host "Real Fleet Data   PASS"
Write-Host "Analytics         PASS"
Write-Host "Alerts            PASS"
Write-Host "Frontend Routing  PASS"
Write-Host "Live Streaming    PASS"
Write-Host "Real-World AI     PASS"
Write-Host "Product Integrity PASS"
Write-Host "`nPROJECT STATUS: READY FOR FINAL FREEZE" -ForegroundColor Green
}catch{Write-Host "`nFINAL ACCEPTANCE: FAILED" -ForegroundColor Red;Write-Host "Reason: $($_.Exception.Message)" -ForegroundColor Red;exit 1}
finally{
if($bf){Stop-Process -Id $bf.Id -Force -ErrorAction SilentlyContinue}
if($ff){Stop-Process -Id $ff.Id -Force -ErrorAction SilentlyContinue}
}



