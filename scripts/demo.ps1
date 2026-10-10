# Run from PowerShell: .\scripts\demo.ps1 [-Monitoring] [-Jenkins] [-Stop]
param([switch]$Monitoring, [switch]$Jenkins, [switch]$Stop)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
# Find standard and per-user Docker Desktop installations without changing PATH globally.
$dockerCommand = Get-Command docker.exe -ErrorAction SilentlyContinue
if ($dockerCommand) { $dockerPath = $dockerCommand.Source }
else {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe",
        "$env:ProgramFiles\Docker\Docker\resources\bin\docker.exe"
    )
    $dockerPath = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $dockerPath) { throw 'Docker CLI not found. Install/start Docker Desktop with Linux containers.' }
function Invoke-Docker {
    & $dockerPath @args
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed (exit $LASTEXITCODE). See output above." }
}
Invoke-Docker version
# Generate random local credentials once; existing env files are preserved.
if (-not $Stop) {
    python scripts/init-env.py
    if ($LASTEXITCODE -ne 0) { throw 'Environment generation failed; install Python 3.' }
}
$composeArgs = @('compose', '-p', 'todo-staging', '--env-file', '.env.staging', '-f', 'docker-compose.yml')
if ($Monitoring) { $composeArgs += @('-f', 'docker-compose.monitoring.yml') }
if ($Stop) {
    Invoke-Docker @composeArgs down
    if ($Jenkins) { Invoke-Docker compose -p todo-ci --env-file .env.production -f jenkins/docker-compose.yml down }
    Write-Host 'Stopped selected demo containers. Named volumes were retained.'
    exit 0
}
# Quiet config validation avoids printing interpolated credentials to the console.
Invoke-Docker @composeArgs config --quiet
Invoke-Docker @composeArgs up -d --build --wait --wait-timeout 240
Invoke-Docker @composeArgs ps
$frontPort = ((Get-Content .env.staging | Where-Object { $_ -match '^FRONTEND_PORT=' }) -split '=', 2)[1]
$baseUrl = "http://localhost:$frontPort"
# The same authenticated smoke workflow is used by Jenkins and the local demo.
python scripts/smoke.py $baseUrl
if ($LASTEXITCODE -ne 0) { throw 'Support portal smoke test failed; inspect the output above.' }
Write-Host 'PASS: support portal authentication, ticket workflow and permissions.' -ForegroundColor Green
if ($Jenkins) { Invoke-Docker compose -p todo-ci --env-file .env.production -f jenkins/docker-compose.yml up -d --build --wait --wait-timeout 240 }
Write-Host "App: $baseUrl"
if ($Monitoring) { Write-Host 'Grafana: http://localhost:3000 | Prometheus: http://localhost:9090' }
if ($Jenkins) { Write-Host 'Jenkins: http://localhost:8088 — complete docs/github-jenkins-setup.md before demonstrating CI/CD.' }
Write-Host 'Keep the successful output for your verification record. Containers remain running for the demo.'
