# PowerShell version of the smoke probe
param(
  [string]$BaseUrl = "http://127.0.0.1:8000"
)
Write-Host "==> Probing $BaseUrl/__debug/routes"
(Invoke-RestMethod -Uri "$BaseUrl/__debug/routes") | Where-Object { $_.path -like "/skips*" } | ConvertTo-Json
Write-Host "==> Probing $BaseUrl/skips/__smoke"
Invoke-RestMethod -Uri "$BaseUrl/skips/__smoke" | ConvertTo-Json
Write-Host "OK"
