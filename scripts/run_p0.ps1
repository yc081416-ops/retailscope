# Resume P0 from the existing project. Stops at the first failed external command.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8 = '1'
$python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
$docker = (Get-Command docker.exe -ErrorAction SilentlyContinue).Source
if (-not $docker) { $docker = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe' }
$env:PATH = (Split-Path $docker -Parent) + ';' + $env:PATH
function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments, [string]$Log)
    # Windows PowerShell treats Docker's ordinary stderr progress as ErrorRecord.
    $ErrorActionPreference = 'Continue'
    & $Program @Arguments 2>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath (Join-Path 'reports' $Log) -ErrorAction Stop
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Program $($Arguments -join ' ') (exit $LASTEXITCODE)" }
}
try {
    Invoke-Checked $python @('-m','retailscope','download-data','--output','reports/download_repeat_manifest.json') 'download_repeat.log'
    Invoke-Checked $python @('-m','retailscope','check-data') 'check_data.log'
    Invoke-Checked $docker @('info','--format','{{.ServerVersion}}') 'docker_engine.log'
    # Generate a local secret only after the engine is available; never print it.
    & $python -c "from pathlib import Path; import secrets; p=Path('.env'); password=secrets.token_hex(24); p.exists() or p.write_text('POSTGRES_DB=retailscope\nPOSTGRES_USER=retailscope\nPOSTGRES_PASSWORD='+password+'\nDATABASE_URL=postgresql://retailscope:'+password+'@localhost:5432/retailscope\n',encoding='utf-8')"
    if ($LASTEXITCODE -ne 0) { throw 'Failed to prepare local database configuration' }
    Invoke-Checked $docker @('compose','up','-d','--wait','db') 'compose_up.log'
    Invoke-Checked $docker @('compose','ps') 'compose_ps.log'
    Invoke-Checked $python @('-m','retailscope','db-status') 'db_status.log'
    Invoke-Checked $python @('-m','retailscope','init-db') 'init_db.log'
    Invoke-Checked $python @('-m','retailscope','verify-import') 'import_verification.log'
    Invoke-Checked $python @('-m','retailscope','db-quality') 'db_quality.log'
    Invoke-Checked $python @('-m','pytest','-q','-rA','--junitxml=reports/pytest.xml') 'pytest.log'
} finally {
    & $python scripts/write_p0_report.py
}
