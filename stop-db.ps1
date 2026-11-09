$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
& (Join-Path $workspace 'work\pg-server\pgsql\bin\pg_ctl.exe') -D (Join-Path $workspace 'work\pgdata') stop -m fast

