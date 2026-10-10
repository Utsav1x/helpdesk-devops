# Run in your own PowerShell if the agent cannot launch Docker: -Repository owner/name.
param([Parameter(Mandatory=$true)][string]$Repository, [string]$GitHubConfig)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$dockerCommand=Get-Command docker.exe -ErrorAction SilentlyContinue
if ($dockerCommand) { $dockerPath=$dockerCommand.Source } else {
    $dockerPath=@("$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe", "$env:ProgramFiles\Docker\Docker\resources\bin\docker.exe") | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $dockerPath) { throw 'Docker CLI not found. Start Docker Desktop in Linux container mode.' }
function Invoke-Docker {
    & $dockerPath @args
    if ($LASTEXITCODE -ne 0) { throw "Docker failed with exit code $LASTEXITCODE; see the output above." }
}
Invoke-Docker version
python scripts/init-env.py
if ($LASTEXITCODE -ne 0) { throw 'Environment initialization failed.' }
$prepareArgs=@('scripts/prepare-jenkins.py','--repository',$Repository)
if ($GitHubConfig) { $prepareArgs+=@('--gh-config',$GitHubConfig) }
python @prepareArgs
if ($LASTEXITCODE -ne 0) { throw 'Jenkins credential preparation failed.' }
# Stop only this repository's Python preview so staging can claim port 8081.
$previewPath=Join-Path $projectRoot 'backend\preview.py'
$previewProcesses=Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($previewPath) }
foreach ($preview in $previewProcesses) { Stop-Process -Id $preview.ProcessId; Write-Host 'Stopped the local SQLite preview for Docker staging.' }
# Validate all application and Jenkins definitions without printing secrets.
Invoke-Docker compose -p todo-production --env-file .env.production config --quiet
Invoke-Docker compose -p todo-staging --env-file .env.staging config --quiet
$ci=@('compose','-p','todo-ci','--env-file','.env.production','-f','jenkins/docker-compose.yml','-f','jenkins/docker-compose.bootstrap.yml')
Invoke-Docker @ci config --quiet
Invoke-Docker @ci up -d --build --wait --wait-timeout 600
Invoke-Docker @ci exec -T jenkins test -f /var/jenkins_home/helpdesk-bootstrap.complete
Write-Host 'Jenkins bootstrap completed. The multibranch job is scanning GitHub and will build main/develop.' -ForegroundColor Green
Write-Host 'Open http://localhost:8088/job/helpdesk/'
Write-Host 'Username: helpdesk-admin. Password: .bootstrap/jenkins-admin-password.txt (keep private).'
Write-Host 'After the branches finish, production is at :8080 and staging at :8081.'
Write-Host 'Changes are detected by a one-minute repository scan. A public webhook is not configured by this command.'
