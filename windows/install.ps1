$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$MonitorDir = Join-Path $env:USERPROFILE ".gemini\agent-monitor"
$DesktopDir = Join-Path $MonitorDir "desktop"
$VenvDir = Join-Path $MonitorDir "venv"
$PrefsFile = Join-Path $MonitorDir "preferences.json"

function Resolve-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            $exe = & py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $exe -and (Test-Path $exe.Trim())) {
                return $exe.Trim()
            }
        } catch {}
    }
    foreach ($cmd in @("python", "python3")) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found) {
            try {
                $verOk = & $found.Source -c "import sys; print(1 if sys.version_info >= (3,9) else 0)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $verOk.Trim() -eq "1") {
                    return $found.Source
                }
            } catch {}
        }
    }
    throw "Python 3.9+ is required. Install Python from https://www.python.org/downloads/ and re-run."
}

$SysPython = Resolve-Python
Write-Host "Using Python: $SysPython"

# Stop running Agent Monitor instances before updating files
Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe' OR Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*agent_monitor.py*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

New-Item -ItemType Directory -Force -Path $MonitorDir, $DesktopDir | Out-Null

# 1. Stage shared scripts & desktop UI
Copy-Item -Force (Join-Path $RepoRoot "Scripts\*.py") $MonitorDir
Copy-Item -Force (Join-Path $RepoRoot "desktop\*.py") $DesktopDir
Copy-Item -Force (Join-Path $RepoRoot "desktop\requirements.txt") $DesktopDir

# 2. Create/update venv with PySide6
if (-not (Test-Path (Join-Path $VenvDir "Scripts\python.exe"))) {
    & $SysPython -m venv $VenvDir
}
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPythonW = Join-Path $VenvDir "Scripts\pythonw.exe"
if (-not (Test-Path $VenvPythonW)) { $VenvPythonW = $VenvPython }

& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install -r (Join-Path $DesktopDir "requirements.txt") --quiet

# 3. Sync provider hooks safely using real system Python
$env:AGENT_MONITOR_PYTHON = $SysPython
$ConfigurePy = Join-Path $MonitorDir "configure-hooks.py"
if (Test-Path $PrefsFile) {
    $Csv = & $SysPython -c "import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8')); ps=[p for p in d.get('enabledProviders',[]) if p in ('antigravity','codex','claude')]; print(','.join(ps) if ps else 'antigravity')" $PrefsFile
    & $SysPython $ConfigurePy sync $Csv | Out-Null
} else {
    & $SysPython $ConfigurePy enable antigravity | Out-Null
}

# 4. Create Startup and Start Menu shortcuts
$AppEntry = Join-Path $DesktopDir "agent_monitor.py"
$StartupDir = [Environment]::GetFolderPath("Startup")
$ProgramsDir = [Environment]::GetFolderPath("Programs")
$WshShell = New-Object -ComObject WScript.Shell

foreach ($TargetDir in @($StartupDir, $ProgramsDir)) {
    if ($TargetDir -and (Test-Path $TargetDir)) {
        $Shortcut = $WshShell.CreateShortcut((Join-Path $TargetDir "Agent Monitor.lnk"))
        $Shortcut.TargetPath = $VenvPythonW
        $Shortcut.Arguments = "`"$AppEntry`""
        $Shortcut.WorkingDirectory = $DesktopDir
        $Shortcut.Description = "Agent Monitor for Antigravity, Codex, and Claude Code"
        $Shortcut.Save()
    }
}

# 5. Launch in background
Start-Process -FilePath $VenvPythonW -ArgumentList "`"$AppEntry`"" -WorkingDirectory $DesktopDir -WindowStyle Hidden

Write-Host "Installed Agent Monitor for Windows!"
Write-Host "Location: $MonitorDir"
Write-Host "Startup shortcut: $(Join-Path $StartupDir 'Agent Monitor.lnk')"
