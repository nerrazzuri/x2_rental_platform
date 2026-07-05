$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$appDir = Join-Path $repoRoot "windows-app"

Push-Location $appDir
try {
    npm run dev
}
finally {
    Pop-Location
}
