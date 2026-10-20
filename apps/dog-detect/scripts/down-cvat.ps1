$ErrorActionPreference = "Stop"
$App = Split-Path -Parent $PSScriptRoot
Set-Location $App

$compose = ".cvat\docker-compose.yml"
if (-not (Test-Path $compose)) {
    $compose = ".cvat\compose.yml"
}
if (-not (Test-Path $compose)) {
    throw "CVAT is not cloned. Run scripts/up-cvat.ps1 first."
}

docker compose -f $compose down
