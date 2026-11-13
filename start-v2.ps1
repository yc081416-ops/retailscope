param([ValidateSet('install','api','web','check')][string]$Action='check')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONUTF8='1'
$python=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Prepare the existing Python 3.12 project environment using start.ps1 -Action init first.' }
if ($Action -eq 'install') {
    & $python -m pip install -r api/requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'API dependency installation failed.' }
    & npm.cmd --prefix frontend ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
} elseif ($Action -eq 'api') {
    & $python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
    exit $LASTEXITCODE
} elseif ($Action -eq 'web') {
    & npm.cmd --prefix frontend run dev
    exit $LASTEXITCODE
} else {
    $data=Invoke-RestMethod 'http://127.0.0.1:8000/api/overview' -TimeoutSec 30
    if (-not $data.metadata.read_only -or $null -eq $data.kpis.orders) { throw 'Overview SQL data check failed.' }
    $page=Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 15
    if ($page.StatusCode -ne 200) { throw 'Frontend unavailable.' }
    Write-Output ('API/SQL ready. Orders: '+$data.kpis.orders+'; frontend: http://127.0.0.1:5173')
}
