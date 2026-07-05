$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python virtual environment not found. Run: python -m venv .venv"
}

& $python -m uvicorn app.main:app --app-dir (Join-Path $repoRoot "local-api") --host 127.0.0.1 --port 8765
