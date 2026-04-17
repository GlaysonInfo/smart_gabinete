$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$hostAddress = if ($env:HOST) { $env:HOST } else { "0.0.0.0" }
$port = if ($env:PORT) { $env:PORT } else { "8012" }
python -m uvicorn apps.api.app.mobile_preview:app --host $hostAddress --port $port --reload