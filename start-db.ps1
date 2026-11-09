$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$bin = Join-Path $workspace 'work\pg-server\pgsql\bin'
$data = Join-Path $workspace 'work\pgdata'
& (Join-Path $bin 'pg_ctl.exe') -D $data status | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host 'PostgreSQL ishlayapti.'; exit 0 }
& (Join-Path $bin 'pg_ctl.exe') -D $data -l (Join-Path $workspace 'work\postgres.log') start

