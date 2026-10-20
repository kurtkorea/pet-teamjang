$ErrorActionPreference = "Stop"
$App = Split-Path -Parent $PSScriptRoot
Set-Location $App

function Find-Python {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) { return $path }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notlike "*WindowsApps*") {
        return $cmd.Source
    }
    return $null
}

$python = Find-Python
if (-not $python) {
    Write-Host "Python 3.12 is not installed. Installing with winget..."
    winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    $python = Find-Python
}
if (-not $python) {
    throw "Python 3.12 was not found. Open a new terminal and run scripts/setup.ps1 again."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

& $python -m pip install -U pip
& $python -m pip install -e .
& $python -m dog_detect gpu --fix
if ($LASTEXITCODE -ne 0) {
    throw "GPU check failed. See the message above."
}
