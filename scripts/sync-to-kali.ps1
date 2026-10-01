$repo = "D:\dsh work\src-high-value-hunter"
$archive = "D:\dsh work\src-high-value-hunter.tar.gz"
$remote = "fmttm@192.168.86.128"
$remoteDir = "~/src-high-value-hunter"

Set-Location $repo
if (Test-Path $archive) { Remove-Item -Force $archive }
tar -czf $archive pyproject.toml README.md config.yaml config.example.yaml .env.example .gitignore src skill docs dsh scripts tests

scp -o BatchMode=yes $archive "${remote}:/tmp/src-high-value-hunter.tar.gz"
ssh -o BatchMode=yes -T $remote "mkdir -p $remoteDir && tar -xzf /tmp/src-high-value-hunter.tar.gz -C $remoteDir"
Write-Host "Synced $repo to ${remote}:$remoteDir"