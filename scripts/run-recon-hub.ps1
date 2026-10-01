$base = "D:\dsh work\src-high-value-hunter"
$env:PYTHONPATH = "$base\src"
& "$base\.venv\Scripts\python.exe" -m recon_hub.server --config "$base\config.yaml"