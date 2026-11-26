# Film Director AI on your own Windows computer: builds and starts the website in Docker, then opens it.
$ErrorActionPreference = "Continue"
Set-Location (Join-Path $PSScriptRoot "..")
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Host "Docker Desktop is not installed. Install it free from https://www.docker.com/products/docker-desktop/ , open it, then run START again." -ForegroundColor Yellow
  Start-Process "https://www.docker.com/products/docker-desktop/"; exit 1
}
docker info *> $null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Starting Docker Desktop... (wait until it says Engine running)" -ForegroundColor Yellow
  $dd = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
  if (Test-Path $dd) { Start-Process $dd }
  for ($i = 0; $i -lt 60; $i++) { Start-Sleep 5; docker info *> $null; if ($LASTEXITCODE -eq 0) { break } }
  if ($LASTEXITCODE -ne 0) { Write-Host "Docker is not running yet. Open Docker Desktop, wait, then run START again." -ForegroundColor Red; exit 1 }
}
$cfg = Join-Path $PSScriptRoot "owner-login.txt"
if (-not (Test-Path $cfg)) {
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $b = New-Object byte[] 48; $rng.GetBytes($b); $key = [Convert]::ToBase64String($b)
  $abc = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"; $p = New-Object byte[] 12; $rng.GetBytes($p)
  $pw = -join ($p | ForEach-Object { $abc[$_ % $abc.Length] })
  Set-Content -Path $cfg -Value @("website: http://localhost:7860", "email: owner@localhost", "password: $pw", "secret: $key")
}
$lines = Get-Content $cfg
$pw = (($lines | Where-Object { $_ -like "password: *" }) -replace "^password: ", "")
$key = (($lines | Where-Object { $_ -like "secret: *" }) -replace "^secret: ", "")
Write-Host "Building the website (first time takes 5-15 minutes)..." -ForegroundColor Cyan
docker build -t film-director-ai -f deploy/huggingface/Dockerfile .
if ($LASTEXITCODE -ne 0) { Write-Host "Build failed. Send the red text above to Claude." -ForegroundColor Red; exit 1 }
docker rm -f film-director-ai *> $null
docker run -d --name film-director-ai --restart unless-stopped -p 7860:7860 -v fda-data:/data -e FDA_ENV=local -e "FDA_OWNER_PASSWORD=$pw" -e "FDA_SECRET_KEY=$key" film-director-ai | Out-Null
Write-Host "Starting..." -ForegroundColor Cyan
for ($i = 0; $i -lt 90; $i++) {
  Start-Sleep 2
  try { if ((Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 http://localhost:7860/api/health).StatusCode -eq 200) { break } } catch {}
}
Write-Host ""
Write-Host "READY:  http://localhost:7860" -ForegroundColor Green
Write-Host "Email:    owner@localhost"
Write-Host "Password: $pw"
Write-Host "(saved in run-local\owner-login.txt; the website starts by itself whenever Docker Desktop is running)"
Start-Process "http://localhost:7860"
