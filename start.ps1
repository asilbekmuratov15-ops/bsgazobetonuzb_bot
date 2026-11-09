$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$python = Join-Path $workspace 'work\venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Python muhiti topilmadi. README bo‘yicha venv yarating.' }
& $python bot.py
