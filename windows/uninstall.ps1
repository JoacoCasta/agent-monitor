$ErrorActionPreference = "SilentlyContinue"

$MonitorDir = Join-Path $env:USERPROFILE ".gemini\agent-monitor"
$ConfigurePy = Join-Path $MonitorDir "configure-hooks.py"

if (Test-Path $ConfigurePy) {
    $PyCmd = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
    foreach ($Prov in @("antigravity", "codex", "claude")) {
        if ($PyCmd -eq "py") {
            & py -3 $ConfigurePy disable $Prov | Out-Null
        } else {
            & $PyCmd $ConfigurePy disable $Prov | Out-Null
        }
    }
}

Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe' OR Name = 'python.exe' OR Name = 'AgentMonitor.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*agent_monitor.py*" -or $_.Name -eq "AgentMonitor.exe" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

$StartupLnk = Join-Path ([Environment]::GetFolderPath("Startup")) "Agent Monitor.lnk"
$ProgramsLnk = Join-Path ([Environment]::GetFolderPath("Programs")) "Agent Monitor.lnk"
Remove-Item -Force -ErrorAction SilentlyContinue $StartupLnk, $ProgramsLnk

if (Test-Path $MonitorDir) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $MonitorDir
}

Write-Host "Agent Monitor uninstalled cleanly."
