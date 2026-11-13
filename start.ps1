[CmdletBinding()]
param(
    [ValidateSet('check','init','start','stop','restart','refresh')][string]$Action='start',
    [string]$PythonExe='',
    [switch]$NoServe
)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONUTF8='1'
$docker=(Get-Command docker.exe -ErrorAction SilentlyContinue).Source
if (-not $docker) { $docker='C:\Program Files\Docker\Docker\resources\bin\docker.exe' }
if (-not (Test-Path -LiteralPath $docker)) { throw '未找到Docker Desktop。请安装并启动WSL 2后端的Docker Desktop。' }
$env:PATH=(Split-Path $docker -Parent)+';'+$env:PATH
function Invoke-Checked {
    param([string]$Program,[string[]]$Arguments)
    $ErrorActionPreference='Continue'
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "命令失败，退出码 $LASTEXITCODE。请检查上方提示；没有执行后续步骤。" }
}
Invoke-Checked $docker @('info','--format','{{.ServerVersion}}')
Invoke-Checked $docker @('compose','version')
if ($Action -eq 'stop') {
    Invoke-Checked $docker @('compose','stop','db')
    Write-Output '数据库已停止，数据卷保留；Streamlit终端用Ctrl+C停止。'
    exit 0
}
$python=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if ($Action -eq 'init') {
    if (-not (Test-Path -LiteralPath $python)) {
        if (-not $PythonExe) {
            $launcher=(Get-Command py.exe -ErrorAction SilentlyContinue).Source
            if (-not $launcher) { throw '请安装Python 3.12，或通过-PythonExe提供python.exe的明确路径。' }
            $PythonExe=(& $launcher -3.12 -c 'import sys; print(sys.executable)').Trim()
            if ($LASTEXITCODE -ne 0) { throw '未找到Python 3.12。' }
        }
        Invoke-Checked $PythonExe @('-m','venv','.venv')
    }
    Invoke-Checked $python @('-c','import sys; assert sys.version_info[:2]==(3,12), "需要Python 3.12"; print(sys.version)')
    Invoke-Checked $python @('-m','pip','install','-r','requirements-lock.txt')
    Invoke-Checked $python @('-m','pip','install','-e','.','--no-deps')
    # Only create the missing file. Never rewrite an existing local password.
    @'
from pathlib import Path
import secrets
p=Path('.env')
if not p.exists():
    password=secrets.token_hex(24)
    with p.open('x',encoding='utf-8') as f:
        f.write('POSTGRES_DB=retailscope\nPOSTGRES_USER=retailscope\nPOSTGRES_PASSWORD='+password+'\nDATABASE_URL=postgresql://retailscope:'+password+'@localhost:5432/retailscope\n')
    print('已创建本地随机密码配置；未输出密码。')
else:
    print('保留现有.env，未修改凭证。')
'@ | & $python -
    if ($LASTEXITCODE -ne 0) { throw '本地配置准备失败。' }
}
if (-not (Test-Path -LiteralPath $python)) { throw '尚无项目虚拟环境，请先运行 .\start.ps1 -Action init。' }
if (-not (Test-Path -LiteralPath '.env')) { throw '尚无.env，请先运行init；不要在聊天中提供密码。' }
Invoke-Checked $python @('-c','import sys; assert sys.version_info[:2]==(3,12), "需要Python 3.12"')
Invoke-Checked $python @('-m','pip','check')
if ($Action -eq 'check') {
    Invoke-Checked $python @('-m','retailscope.runtime','check')
    exit 0
}
if ($Action -eq 'restart') { Invoke-Checked $docker @('compose','stop','db') }
Invoke-Checked $docker @('compose','up','-d','--wait','db')
$runtimeAction=if ($Action -eq 'init') {'init'} elseif ($Action -eq 'refresh') {'refresh'} else {'check'}
Invoke-Checked $python @('-m','retailscope.runtime',$runtimeAction)
if (($Action -eq 'start' -or $Action -eq 'restart') -and -not $NoServe) {
    Write-Output '系统数据与分析检查通过。打开 http://127.0.0.1:8501；停止页面服务用Ctrl+C。'
    Invoke-Checked $python @('-m','streamlit','run','app/Home.py')
}
