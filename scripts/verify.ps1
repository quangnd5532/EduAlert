param([string]$PythonExe = '')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not $PythonExe) {
    foreach ($eduCandidate in @('.venv312/Scripts/python.exe', '.venv313/Scripts/python.exe', '.venv/Scripts/python.exe')) {
        if (Test-Path -LiteralPath $eduCandidate) { $PythonExe = Join-Path (Get-Location) $eduCandidate; break }
    }
}
if (-not $PythonExe) { throw 'Chạy start.ps1 để tạo môi trường, hoặc truyền -PythonExe.' }
$eduPython = $PythonExe
& $eduPython -m compileall -q app migrations scripts tests
if ($LASTEXITCODE -ne 0) { throw 'Có lỗi cú pháp Python.' }
& $eduPython -m unittest tests.test_assessment tests.test_demo_data tests.test_portal_data -v
if ($LASTEXITCODE -ne 0) { throw 'Kiểm thử thuật toán thất bại.' }
if (Get-Command node -ErrorAction SilentlyContinue) {
    node --check static/portal.js
    if ($LASTEXITCODE -ne 0) { throw 'Có lỗi cú pháp JavaScript.' }
    node --test tests/frontend.test.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Kiểm thử frontend thất bại.' }
} else {
    Write-Output 'Không có Node: chưa chạy kiểm thử frontend; website không cần Node để khởi động.'
}
& $eduPython -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Kiểm thử tích hợp chưa đạt.' }
& $eduPython scripts/check_environment.py
if ($LASTEXITCODE -ne 0) { throw 'Thiếu phụ thuộc hoặc Chart.js cục bộ.' }
