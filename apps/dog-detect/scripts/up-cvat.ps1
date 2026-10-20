$ErrorActionPreference = "Stop"
$App = Split-Path -Parent $PSScriptRoot
Set-Location $App

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker was not found. Install Docker Desktop and start it."
}

$ref = if ($env:CVAT_REF) { $env:CVAT_REF } else { "v2.79.0" }
if (-not (Test-Path ".cvat\.git")) {
    git clone --depth 1 --branch $ref https://github.com/cvat-ai/cvat.git .cvat
}

$compose = ".cvat\docker-compose.yml"
if (-not (Test-Path $compose)) {
    $compose = ".cvat\compose.yml"
}
if (-not (Test-Path $compose)) {
    throw "CVAT compose file was not found in .cvat"
}

docker compose -f $compose up -d

Write-Host "Waiting for CVAT database migrations..."
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    docker exec cvat_server python manage.py migrate --check 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 5
}
if (-not $ready) {
    throw "CVAT migrations did not finish. Check logs with: docker logs cvat_server"
}

Write-Host "CVAT: http://localhost:8080"
Write-Host "Create the admin user, then put the password in .env:"
Write-Host "  docker exec -it cvat_server python manage.py createsuperuser"
