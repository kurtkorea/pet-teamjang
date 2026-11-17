$ErrorActionPreference = "Stop"
$App = Split-Path -Parent $PSScriptRoot
Set-Location $App

$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { throw "python 이 없습니다." }

if (-not (Test-Path ".env")) {
    if (Test-Path "..\dog-detect\.env") {
        Copy-Item "..\dog-detect\.env" ".env"
        Write-Host "Copied .env from dog-detect"
    } else {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from example — fill CVAT_PASSWORD"
    }
}

& $python -m pip install -U pip
& $python -m pip install -e ..\dog-detect
& $python -m pip install -e .
Write-Host "OK: maxi-dog-detect installed"
Write-Host "Next: python -m maxi_dog_detect import-maix"
