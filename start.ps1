[CmdletBinding()]
param(
    [string]$PythonExe = '',
    [ValidateRange(1024, 65535)][int]$Port = 8001,
    [switch]$Demo
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Get-EduPythonVersion {
    param([string]$Executable)
    try {
        if (-not (Test-Path -LiteralPath $Executable -ErrorAction Stop)) { return '' }
        $eduVersionCode = "import sys; print('%s.%s' % sys.version_info[:2])"
        $eduVersion = & $Executable -c $eduVersionCode 2>$null
        if ($LASTEXITCODE -eq 0) { return ([string]$eduVersion).Trim() }
    } catch [System.UnauthorizedAccessException] {
        throw "Khong duoc phep doc/chay '$Executable'. Hay chay start.ps1 trong PowerShell thong thuong ngoai moi truong cong cu; khong can cai lai Python chi vi loi quyen nay."
    } catch { }
    return ''
}

function Find-EduPython {
    $eduBlockedPaths = @()
    foreach ($eduTag in @('3.12', '3.13')) {
        if (Get-Command py -ErrorAction SilentlyContinue) {
            try {
                $eduPath = & py "-$eduTag" -c 'import sys; print(sys.executable)' 2>$null
                if ($LASTEXITCODE -eq 0 -and $eduPath) { return ([string]$eduPath).Trim() }
            } catch { }
        }
        $eduCompact = $eduTag.Replace('.', '')
        $eduRuntimePaths = @(
            (Join-Path $env:LOCALAPPDATA "Python/pythoncore-$eduTag-64/python.exe"),
            (Join-Path $env:LOCALAPPDATA "Programs/Python/Python$eduCompact/python.exe"),
            (Join-Path $env:ProgramFiles "Python$eduCompact/python.exe"),
            (Join-Path $env:SystemDrive "Python$eduCompact/python.exe")
        )
        foreach ($eduRuntimePath in $eduRuntimePaths) {
            try {
                if ((Test-Path -LiteralPath $eduRuntimePath -ErrorAction Stop) -and (Get-EduPythonVersion $eduRuntimePath) -eq $eduTag) {
                    return $eduRuntimePath
                }
            } catch { $eduBlockedPaths += $eduRuntimePath }
        }
    }
    foreach ($eduCandidate in @(
        (Join-Path $PSScriptRoot '.runtime/python312/python.exe'),
        (Join-Path $PSScriptRoot '.venv312/Scripts/python.exe'),
        (Join-Path $PSScriptRoot '.venv313/Scripts/python.exe'),
        (Join-Path $PSScriptRoot '.venv/Scripts/python.exe')
    )) {
        try {
            if ((Test-Path -LiteralPath $eduCandidate -ErrorAction Stop) -and (Get-EduPythonVersion $eduCandidate) -in @('3.12', '3.13')) {
                return $eduCandidate
            }
        } catch { $eduBlockedPaths += $eduCandidate }
    }
    if ($eduBlockedPaths.Count -gt 0) {
        throw ("Khong kiem tra duoc quyen truy cap Python tai: " + ($eduBlockedPaths -join ', ') + ". Python co the da cai thanh cong. Chay script trong PowerShell thong thuong ngoai moi truong cong cu; khong cai lai chi vi thong bao nay.")
    }
    return ''
}

try {
    try {
        $eduRunning = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2
        if ($eduRunning.application -eq 'edualert' -and $eduRunning.version -eq '3.1.0' -and $eduRunning.status -eq 'ok') {
            Write-Host "EduAlert da san sang. Uvicorn running on http://127.0.0.1:$Port"
            exit 0
        }
    } catch { }
    if (-not $PythonExe) { $PythonExe = Find-EduPython }
    if (-not $PythonExe) {
        throw @'
Khong tim thay Python 3.12 hoac 3.13. Moi truong .venv Python 3.15 cu duoc giu nguyen.
Cai truc tiep Python 3.12 x64: https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
Chon Install Now; khong chi cai Python Install Manager.
Sau khi cai, mo terminal moi va chay: .\start.ps1 -Demo
Neu Python duoc cai o vi tri rieng: .\start.ps1 -PythonExe 'C:\duong-dan\python.exe' -Demo
'@
    }

    $eduVersion = Get-EduPythonVersion $PythonExe
    if ($eduVersion -notin @('3.12', '3.13')) {
        throw "Python '$PythonExe' la phien ban '$eduVersion'. Du an nay can Python 3.12/3.13; khong tai dung .venv 3.15."
    }
    $eduVenv = Join-Path $PSScriptRoot ('.venv' + $eduVersion.Replace('.', ''))
    $eduPython = Join-Path $eduVenv 'Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $eduPython)) {
        Write-Host "Tao moi truong $eduVenv (giu nguyen moi truong cu)..."
        & $PythonExe -m venv $eduVenv
        if ($LASTEXITCODE -ne 0) { throw 'Tao virtualenv that bai.' }
    }
    if ((Get-EduPythonVersion $eduPython) -ne $eduVersion) { throw 'Virtualenv khong dung phien ban Python. Chon lai -PythonExe.' }

    $eduDependencyCheck = "import importlib.metadata as m; from pathlib import Path; req=[r.strip().split('==') for r in Path('requirements.txt').read_text().splitlines() if r.strip() and not r.startswith('#')]; assert all(m.version(n)==v for n,v in req)"
    try {
        & $eduPython -c $eduDependencyCheck 2>$null
        $eduNeedsInstall = $LASTEXITCODE -ne 0
    } catch { $eduNeedsInstall = $true }
    if ($eduNeedsInstall) {
        Write-Host 'Cai phu thuoc (can ket noi PyPI lan dau)...'
        & $eduPython -m pip install -r requirements.txt --retries 1 --timeout 15
        if ($LASTEXITCODE -ne 0) { throw 'Khong tai/cai duoc thu vien. Neu co WinError 10013, ket noi mang cua tien trinh bi chan; server CHUA chay.' }
    }

    $eduMissingAssets = @('chart.umd.js', 'swagger-ui-bundle.js', 'swagger-ui.css') | Where-Object {
        -not (Test-Path -LiteralPath (Join-Path $PSScriptRoot "static/vendor/$_"))
    }
    if ($eduMissingAssets) {
        Write-Host 'Cai Chart.js va Swagger UI vao static/vendor...'
        & $eduPython scripts/vendor_assets.py
        if ($LASTEXITCODE -ne 0) { throw 'Chua tai duoc tai nguyen cuc bo. Server CHUA chay.' }
    }
    & $eduPython -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Migration that bai. Server CHUA chay.' }

    if ($Demo -or $env:EDUALERT_DEMO -eq 'true') {
        $env:EDUALERT_DEMO = 'true'
        $eduPromptedPassword = $false
        if (-not $env:EDUALERT_DEMO_PASSWORD) {
            $eduAdminCheck = "from app.db import SessionLocal; from app.models import User; from sqlalchemy import select; db=SessionLocal(); exists=db.scalar(select(User.id).where(User.username=='admin')); db.close(); raise SystemExit(0 if exists else 1)"
            & $eduPython -c $eduAdminCheck
            if ($LASTEXITCODE -ne 0) {
                $eduSecurePassword = Read-Host 'Tao mat khau DEMO cho admin/advisor1/advisor2 (10-128 ky tu)' -AsSecureString
                try { $env:EDUALERT_DEMO_PASSWORD = [System.Net.NetworkCredential]::new('', $eduSecurePassword).Password }
                finally { $eduSecurePassword.Dispose() }
                $eduPromptedPassword = $true
            }
        }
        try {
            & $eduPython -m app.seed
            if ($LASTEXITCODE -ne 0) { throw 'Seed that bai. Mat khau demo can 10-128 ky tu.' }
        } finally {
            if ($eduPromptedPassword) { Remove-Item Env:EDUALERT_DEMO_PASSWORD -ErrorAction SilentlyContinue }
        }
    }

    Write-Host "EDUALERT_STARTING"
    Write-Host "Dia chi: http://127.0.0.1:$Port - chi mo sau khi co 'Uvicorn running on'. Ctrl+C de dung."
    & $eduPython -m uvicorn app.main:app --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { throw "Uvicorn khong khoi dong duoc. Neu cong $Port dang ban, chon cong trong bang tham so -Port." }
} catch {
    Write-Host ("EDUALERT_ERROR: " + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
