param(
    [int]$Port = 10095
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not installed or not on PATH."
}

$env:PORT = $Port
docker compose up -d --build
Write-Host "FunASR is starting on http://127.0.0.1:$Port"
