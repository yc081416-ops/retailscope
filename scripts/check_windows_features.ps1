# Run elevated only to inspect the two features required by WSL 2.
$ErrorActionPreference = 'Stop'
$report = Join-Path $PSScriptRoot '..\reports\windows_features.json'
$features = foreach ($name in 'VirtualMachinePlatform', 'Microsoft-Windows-Subsystem-Linux') {
    Get-WindowsOptionalFeature -Online -FeatureName $name
}
$features |
    Select-Object FeatureName, @{Name='State'; Expression={$_.State.ToString()}} |
    ConvertTo-Json | Set-Content -LiteralPath $report -Encoding UTF8
