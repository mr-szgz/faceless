# Faceless Installer for Windows PowerShell
# Usage:  iwr https://raw.githubusercontent.com/mr-szgz/faceless/main/install.ps1 | iex
# Local:  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\install.ps1 --local
# NoTorch: .\install.ps1 --no-torch
# Test:   .\install.ps1 --package faceless

function Install-Faceless {
    $ErrorActionPreference = "Stop"
    $script:FacelessVerbose = ($env:FACELESS_VERBOSE -eq "1")

    # -- Parse flags --
    $FacelessLocalInstall = $false
    $PackageName = "faceless"
    $RepoRoot = ""
    $SkipTorch = $false

    $argList = $args
    for ($i = 0; $i -lt $argList.Count; $i++) {
        switch ($argList[$i]) {
            "--local"    { $FacelessLocalInstall = $true }
            "--no-torch" { $SkipTorch = $true }
            "--verbose"  { $script:FacelessVerbose = $true }
            "-v"         { $script:FacelessVerbose = $true }
            "--package"  {
                $i++
                if ($i -ge $argList.Count) {
                    Write-Host "[ERROR] --package requires an argument." -ForegroundColor Red
                    return
                }
                $PackageName = $argList[$i]
            }
        }
    }

    if ($script:FacelessVerbose) {
        $env:FACELESS_VERBOSE = "1"
    }

    if ($FacelessLocalInstall) {
        $RepoRoot = (Resolve-Path (Split-Path -Parent $PSCommandPath)).Path
        if (-not (Test-Path (Join-Path $RepoRoot "pyproject.toml"))) {
            Write-Host "[ERROR] --local must be run from the faceless repo root (pyproject.toml not found at $RepoRoot)" -ForegroundColor Red
            return
        }
    }

    $PythonVersion = "3.10"
    $FacelessHome = Join-Path $env:USERPROFILE ".faceless"
    $VenvDir = Join-Path $FacelessHome ".venv"

    function step {
        param(
            [Parameter(Mandatory = $true)][string]$Label,
            [Parameter(Mandatory = $true)][string]$Value,
            [string]$Color = "Green"
        )
        $padded = if ($Label.Length -ge 15) { $Label.Substring(0, 15) } else { $Label.PadRight(15) }
        Write-Host ("  {0}" -f $padded) -NoNewline -ForegroundColor DarkGray
        $fc = switch ($Color) {
            "Green" { "DarkGreen" }
            "Yellow" { "Yellow" }
            "Red" { "Red" }
            default { "DarkGreen" }
        }
        Write-Host $Value -ForegroundColor $fc
    }

    function substep {
        param(
            [Parameter(Mandatory = $true)][string]$Message,
            [string]$Color = "DarkGray"
        )
        $fc = switch ($Color) {
            "Yellow" { "Yellow" }
            "Red" { "Red" }
            default { "DarkGray" }
        }
        Write-Host ("  {0,-15}{1}" -f "", $Message) -ForegroundColor $fc
    }

    function Refresh-SessionPath {
        $machine = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
        $user = [System.Environment]::GetEnvironmentVariable("Path", "User")
        $merged = "$machine;$user;$env:Path"
        $seen = @{}
        $unique = @()
        foreach ($p in $merged -split ";") {
            $key = $p.TrimEnd("\").ToLowerInvariant()
            if ($key -and -not $seen.ContainsKey($key)) {
                $seen[$key] = $true
                $unique += $p
            }
        }
        $env:Path = $unique -join ";"
    }

    function Invoke-InstallCommand {
        param([Parameter(Mandatory = $true)][ScriptBlock]$Command)
        $prevEap = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $global:LASTEXITCODE = 0
            if ($script:FacelessVerbose) {
                & $Command 2>&1 | Out-Host
            } else {
                $output = & $Command 2>&1 | Out-String
                if ($LASTEXITCODE -ne 0) {
                    Write-Host $output -ForegroundColor Red
                }
            }
            return [int]$LASTEXITCODE
        } finally {
            $ErrorActionPreference = $prevEap
        }
    }

    function Test-IsCondaPython {
        param([string]$Exe)
        $condaPattern = "(?i)(conda|miniconda|anaconda|miniforge|mambaforge)"
        if ($Exe -match $condaPattern) { return $true }
        try {
            $basePrefix = (& $Exe -c "import sys; print(sys.base_prefix)" 2>$null | Out-String).Trim()
            if ($basePrefix -match $condaPattern) { return $true }
        } catch { }
        return $false
    }

    function Find-CompatiblePython {
        $pyLauncher = Get-Command py -CommandType Application -ErrorAction SilentlyContinue
        if ($pyLauncher) {
            try {
                $out = & $pyLauncher.Source "-3.10" --version 2>&1 | Out-String
                if ($out -match "Python (3\.10)\.\d+") {
                    $resolvedExe = (& $pyLauncher.Source "-3.10" -c "import sys; print(sys.executable)" 2>$null | Out-String).Trim()
                    if ($resolvedExe -and (Test-Path $resolvedExe) -and -not (Test-IsCondaPython $resolvedExe)) {
                        return @{ Version = "3.10"; Path = $resolvedExe }
                    }
                }
            } catch { }
        }

        foreach ($name in @("python3", "python")) {
            foreach ($cmd in @(Get-Command $name -All -ErrorAction SilentlyContinue)) {
                if (-not $cmd.Source) { continue }
                if ($cmd.Source -like "*\WindowsApps\*") { continue }
                if (Test-IsCondaPython $cmd.Source) { continue }
                try {
                    $out = & $cmd.Source --version 2>&1 | Out-String
                    if ($out -match "Python (3\.10)\.\d+") {
                        return @{ Version = "3.10"; Path = $cmd.Source }
                    }
                } catch { }
            }
        }
        return $null
    }

    function New-FacelessShortcuts {
        param([Parameter(Mandatory = $true)][string]$RunFacelessExePath)
        if (-not (Test-Path $RunFacelessExePath)) {
            substep "cannot create shortcuts, run_faceless.exe not found at $RunFacelessExePath" "Yellow"
            return
        }
        try {
            $desktopDir = [Environment]::GetFolderPath("Desktop")
            if (-not $desktopDir -or [string]::IsNullOrWhiteSpace($desktopDir)) {
                substep "Desktop path unavailable; skipped desktop shortcut creation" "Yellow"
                return
            }
            $linkPath = Join-Path $desktopDir "Faceless.lnk"
            $target = (Resolve-Path $RunFacelessExePath).Path
            $wshell = New-Object -ComObject WScript.Shell
            $shortcut = $wshell.CreateShortcut($linkPath)
            $shortcut.TargetPath = $target
            $shortcut.Arguments = "--help"
            $shortcut.Description = "Launch Faceless"
            $shortcut.IconLocation = "$target,0"
            $shortcut.Save()
            substep "Created Faceless desktop shortcut"
        } catch {
            substep "shortcut setup failed; skipping shortcuts: $($_.Exception.Message)" "Yellow"
        }
    }

    Write-Host ""
    Write-Host "  Faceless Installer (Windows)" -ForegroundColor DarkGreen
    Write-Host ""

    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        step "winget" "not available" "Red"
        substep "Install it from https://aka.ms/getwinget" "Yellow"
        return
    }

    $DetectedPython = Find-CompatiblePython
    if ($DetectedPython) {
        step "python" "Python $($DetectedPython.Version) already installed"
    } else {
        substep "installing Python ${PythonVersion}..."
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            winget install -e --id "Python.Python.$PythonVersion" --accept-package-agreements --accept-source-agreements
        } catch { }
        $ErrorActionPreference = $prevEAP
        Refresh-SessionPath
        $DetectedPython = Find-CompatiblePython
        if (-not $DetectedPython) {
            Write-Host "[ERROR] Python 3.10 was not found after install attempt." -ForegroundColor Red
            return
        }
    }

    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        substep "installing uv package manager..."
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            winget install --id=astral-sh.uv -e --accept-package-agreements --accept-source-agreements
        } catch { }
        $ErrorActionPreference = $prevEAP
        Refresh-SessionPath
    }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        substep "trying alternative uv installer..." "Yellow"
        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try { powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex" } catch { }
        $ErrorActionPreference = $prevEAP
        Refresh-SessionPath
    }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        step "uv" "could not be installed" "Red"
        return
    }

    if (-not (Test-Path $FacelessHome)) {
        New-Item -ItemType Directory -Path $FacelessHome -Force | Out-Null
    }

    $VenvPython = Join-Path $VenvDir "Scripts\python.exe"
    if (Test-Path $VenvPython) {
        substep "removing existing environment for fresh install..."
        Remove-Item -Recurse -Force $VenvDir
    }

    if (-not (Test-Path $VenvPython)) {
        step "venv" "creating Python $($DetectedPython.Version) virtual environment"
        $venvExit = Invoke-InstallCommand { uv venv $VenvDir --python "$($DetectedPython.Path)" }
        if ($venvExit -ne 0) {
            Write-Host "[ERROR] Failed to create virtual environment (exit code $venvExit)" -ForegroundColor Red
            return
        }
    }

    $nvidiaSmiCmd = $null
    try { $nvidiaSmiCmd = (Get-Command nvidia-smi -ErrorAction SilentlyContinue).Source } catch { }
    if (-not $nvidiaSmiCmd) {
        foreach ($candidate in @("$env:ProgramFiles\NVIDIA Corporation\NVSMI\nvidia-smi.exe", "$env:SystemRoot\System32\nvidia-smi.exe")) {
            if (Test-Path $candidate) { $nvidiaSmiCmd = $candidate; break }
        }
    }
    $TorchIndexUrl = "https://download.pytorch.org/whl/cpu"
    if ($nvidiaSmiCmd -and (Test-Path $nvidiaSmiCmd)) {
        $TorchIndexUrl = "https://download.pytorch.org/whl/cu128"
        step "gpu" "NVIDIA GPU detected"
    } else {
        step "gpu" "none (CPU-only mode)" "Yellow"
    }

    if (-not $SkipTorch) {
        substep "installing PyTorch ($TorchIndexUrl)..."
        $torchExit = Invoke-InstallCommand { uv pip install --python $VenvPython "torch>=2.4,<2.11.0" torchvision torchaudio --index-url $TorchIndexUrl }
        if ($torchExit -ne 0) {
            Write-Host "[ERROR] Failed to install PyTorch (exit code $torchExit)" -ForegroundColor Red
            return
        }
    } else {
        substep "skipping PyTorch (--no-torch flag set)." "Yellow"
    }

    substep "installing faceless package..."
    if ($FacelessLocalInstall) {
        $installExit = Invoke-InstallCommand { uv pip install --python $VenvPython -e $RepoRoot }
    } else {
        $installExit = Invoke-InstallCommand { uv pip install --python $VenvPython --upgrade-package faceless "$PackageName" }
    }
    if ($installExit -ne 0) {
        Write-Host "[ERROR] Failed to install faceless (exit code $installExit)" -ForegroundColor Red
        return
    }

    $FacelessExe = Join-Path $VenvDir "Scripts\faceless.exe"
    if (-not (Test-Path $FacelessExe)) {
        Write-Host "[ERROR] faceless CLI was not installed correctly." -ForegroundColor Red
        Write-Host "        Expected: $FacelessExe" -ForegroundColor Yellow
        return
    }

    $RunFacelessExe = Join-Path $VenvDir "Scripts\run_faceless.exe"
    if (Test-Path $RunFacelessExe) {
        New-FacelessShortcuts -RunFacelessExePath $RunFacelessExe
    } else {
        substep "run_faceless.exe not found; skipped shortcut creation" "Yellow"
    }

    step "verify" "running faceless --help"
    $helpExit = Invoke-InstallCommand { & $FacelessExe --help }
    if ($helpExit -ne 0) {
        Write-Host "[ERROR] faceless help command failed (exit code $helpExit)" -ForegroundColor Red
        return
    }

    $ScriptsDir = Join-Path $VenvDir "Scripts"
    $UserPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    if (-not $UserPath -or $UserPath -notlike "*$ScriptsDir*") {
        if ($UserPath) {
            [System.Environment]::SetEnvironmentVariable("Path", "$ScriptsDir;$UserPath", "User")
        } else {
            [System.Environment]::SetEnvironmentVariable("Path", "$ScriptsDir", "User")
        }
        Refresh-SessionPath
        step "path" "added faceless to PATH"
    }

    step "done" "Faceless install complete"
    step "launch" "manual commands:"
    substep "& `"$VenvDir\Scripts\Activate.ps1`""
    substep "faceless --help"
    substep "run_faceless --help"
    Write-Host ""
}

Install-Faceless @args
