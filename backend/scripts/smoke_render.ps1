# file: backend/scripts/smoke_render.ps1
# Purpose: end-to-end driver-flow smoke on Render
# Usage:
#   $env:BASE="https://<service>.onrender.com"
#   $env:API="<driver-api-key>"      # only if prod requires it
#   powershell -ExecutionPolicy Bypass -File .\backend\scripts\smoke_render.ps1
param(
  [string]$Base   = $env:BASE,
  [string]$ApiKey = $env:API,
  [string]$QR     = "QR123",
  [string]$Driver = "Alex",
  [string]$Vehicle = "TEST-001",
  [string]$ZoneA  = "ZONE_A",
  [string]$ZoneB  = "ZONE_B",
  [string]$ZoneC  = "ZONE_C"
)

if (-not $Base) { throw "Set BASE env var or pass -Base 'https://<service>.onrender.com'" }

$ErrorActionPreference = "Stop"
$H = @{ "Content-Type" = "application/json" }
if ($ApiKey) { $H["X-API-Key"] = $ApiKey }

function CallJson([string]$Url, [string]$Method = "GET", $Body = $null) {
  try {
    if ($Body) { return Invoke-RestMethod -Uri $Url -Method $Method -Headers $H -Body ($Body | ConvertTo-Json) }
    else      { return Invoke-RestMethod -Uri $Url -Method $Method -Headers $H }
  } catch {
    Write-Warning "$Method $Url => $($_.Exception.Message)"
    return $null
  }
}

Write-Host "== routes"
$routes = CallJson "$Base/__debug/routes"
if ($routes) { $routes | ConvertTo-Json -Depth 5 | Write-Host }

Write-Host "== skips smoke"
$smoke = CallJson "$Base/skips/__smoke"
if ($smoke) { $smoke | ConvertTo-Json | Write-Host }

Write-Host "== ensure skip"
CallJson "$Base/driver/dev/ensure-skip?qr=$QR" "GET" | Out-Null

Write-Host "== scan"
$scan = CallJson "$Base/driver/scan?q=$QR" "GET"
if ($scan) { $scan | ConvertTo-Json | Write-Host }

Write-Host "== deliver-empty"
$deliver = CallJson "$Base/driver/deliver-empty" "POST" @{ skip_qr=$QR; to_zone_id=$ZoneA; driver_name=$Driver; vehicle_reg=$Vehicle }
if ($deliver) { $deliver | ConvertTo-Json | Write-Host }

Write-Host "== relocate-empty"
$reloc = CallJson "$Base/driver/relocate-empty" "POST" @{ skip_qr=$QR; to_zone_id=$ZoneB; driver_name=$Driver }
if ($reloc) { $reloc | ConvertTo-Json | Write-Host }

Write-Host "== collect-full"
$collect = CallJson "$Base/driver/collect-full" "POST" @{
  skip_qr=$QR; destination_type="RECYCLING"; destination_name="ECO MRF";
  weight_source="WEIGHBRIDGE"; gross_kg=2500; tare_kg=1500; driver_name=$Driver; site_id="SITE1"
}
if ($collect) {
  $collect | ConvertTo-Json | Write-Host
  if ($collect.wtn_pdf_url) {
    $pdf = "$Base$($collect.wtn_pdf_url)"
    Write-Host "Opening PDF: $pdf"
    Start-Process $pdf
  }
}

Write-Host "== return-empty"
$return = CallJson "$Base/driver/return-empty" "POST" @{ skip_qr=$QR; to_zone_id=$ZoneC; driver_name=$Driver }
if ($return) { $return | ConvertTo-Json | Write-Host }
