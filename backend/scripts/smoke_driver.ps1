# path: backend/scripts/smoke_driver.ps1
param(
  [string]$Base = "http://localhost:8000",
  [string]$Qr   = "QR123"
)

$ErrorActionPreference = 'Stop'
$headers = @{ 'Content-Type' = 'application/json' }

function Invoke-JsonPostonPost {
  param([string]$Url, [hashtable]$Body)
  try {
    $json = ($Body | ConvertTo-Json -Depth 6)
    return Invoke-RestMethod -Method POST -Uri $Url -Headers $headers -Body $json
  } catch {
    if ($_.Exception.Response) {
      $status = $_.Exception.Response.StatusCode.value__
      $stream = $_.Exception.Response.GetResponseStream()
      $reader = New-Object IO.StreamReader($stream)
      $text = $reader.ReadToEnd()
      Write-Warning "POST $Url -> $status $text"
      return $null
    } else { throw }
  }
}

Write-Host "[0] ensure skip exists ($Qr)"
# Dev helper (if present); ignore failures if endpoint is disabled
try { Invoke-RestMethod -Method POST -Uri "$Base/driver/dev/ensure-skip" -Headers $headers -Body (@{ qr_code = $Qr } | ConvertTo-Json) } catch { Write-Warning $_ }

Write-Host "[1] scan"
Invoke-RestMethod -Uri "$Base/driver/scan?qr=$Qr"

Write-Host "[2] deliver-empty"
$r2 = Invoke-JsonPost "$Base/driver/deliver-empty" @{ skip_qr=$Qr; to_zone_id='ZONE_A'; driver_name='Alex'; vehicle_reg='TEST-001' }
$r2

Write-Host "[3] relocate-empty (A -> B)"
$r3 = Invoke-JsonPost "$Base/driver/relocate-empty" @{ skip_qr=$Qr; to_zone_id='ZONE_B'; driver_name='Alex' }
$r3

Write-Host "[4] collect-full (weight + WTN)"
$r4 = Invoke-JsonPost "$Base/driver/collect-full" @{ skip_qr=$Qr; destination_type='RECYCLING'; destination_name='Eco MRF'; weight_source='WEIGHBRIDGE'; gross_kg=2500; tare_kg=1500; driver_name='Alex'; site_id='SITE1' }
$r4

Write-Host "[5] return-empty (to C)"
$r5 = Invoke-JsonPost "$Base/driver/return-empty" @{ skip_qr=$Qr; to_zone_id='ZONE_C'; driver_name='Alex' }
$r5

Write-Host "Done. movement_ids:" ($r2.id, $r3.id, $r4.movement_id, $r5.id -join ', ')
