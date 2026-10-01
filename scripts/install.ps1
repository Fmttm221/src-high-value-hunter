$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

if (Get-Command uv -ErrorAction SilentlyContinue) {
  uv venv .venv
  uv pip install --python .\.venv\Scripts\python.exe --no-cache "mcp<2" httpx pyyaml
} else {
  python -m venv .venv
  .\.venv\Scripts\python.exe -m pip install --upgrade pip
  .\.venv\Scripts\python.exe -m pip install "mcp<2" httpx pyyaml
}

Write-Host "Install complete."
Write-Host "Next:"
Write-Host "  1. copy config.example.yaml to config.yaml"
Write-Host "  2. fill config/targets.yaml"
Write-Host "  3. register dsh/recon-hub.yml"
Write-Host "  4. run scripts/run-recon-hub.ps1"