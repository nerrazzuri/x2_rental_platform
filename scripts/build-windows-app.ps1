$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$appDir = Join-Path $repoRoot "windows-app"
$cargoBin = Join-Path $env:USERPROFILE ".cargo\bin"
$vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"

if (-not (Test-Path -LiteralPath (Join-Path $cargoBin "cargo.exe"))) {
    throw "cargo.exe was not found in $cargoBin"
}

if (-not (Test-Path -LiteralPath $vswhere)) {
    throw "vswhere.exe was not found. Install Visual Studio Build Tools with the C++ toolchain."
}

$vsInstall = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vsInstall) {
    throw "Visual Studio Build Tools with the C++ toolchain was not found."
}

$msvcRoot = Get-ChildItem -Directory -LiteralPath (Join-Path $vsInstall "VC\Tools\MSVC") |
    Sort-Object Name -Descending |
    Select-Object -First 1
if (-not $msvcRoot) {
    throw "MSVC tools directory was not found under $vsInstall"
}

$sdkLibRoot = Join-Path ${env:ProgramFiles(x86)} "Windows Kits\10\Lib"
$sdkIncludeRoot = Join-Path ${env:ProgramFiles(x86)} "Windows Kits\10\Include"
$sdkVersion = Get-ChildItem -Directory -LiteralPath $sdkLibRoot |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "um\x64\kernel32.lib") } |
    Sort-Object Name -Descending |
    Select-Object -First 1
if (-not $sdkVersion) {
    throw "Windows SDK kernel32.lib was not found. Install a Windows 10 or Windows 11 SDK."
}

$env:Path = "$cargoBin;$($msvcRoot.FullName)\bin\Hostx64\x64;$env:Path"
$env:LIB = "$($msvcRoot.FullName)\lib\x64;$($sdkVersion.FullName)\um\x64;$($sdkVersion.FullName)\ucrt\x64;$env:LIB"
$env:INCLUDE = "$($msvcRoot.FullName)\include;$sdkIncludeRoot\$($sdkVersion.Name)\um;$sdkIncludeRoot\$($sdkVersion.Name)\ucrt;$sdkIncludeRoot\$($sdkVersion.Name)\shared;$sdkIncludeRoot\$($sdkVersion.Name)\winrt;$env:INCLUDE"

Push-Location $appDir
try {
    npm run tauri -- build
}
finally {
    Pop-Location
}
