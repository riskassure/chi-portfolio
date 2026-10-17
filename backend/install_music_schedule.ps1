# Run locally to register this user's Spotify refresh task. No password is stored.
$ErrorActionPreference = 'Stop'
$musicSource = Join-Path $PSScriptRoot 'src'
$musicStateFile = Join-Path (Split-Path $PSScriptRoot) 'dist/math-workflow.json'
$musicState = Get-Content -LiteralPath $musicStateFile -Raw | ConvertFrom-Json
$musicDatabase = [System.IO.Path]::GetFullPath($musicState.working)
if (-not (Test-Path -LiteralPath $musicDatabase -PathType Leaf)) { throw 'The working database is missing.' }
$musicPython = (Get-Command python.exe).Source
$musicPythonWindowless = Join-Path (Split-Path $musicPython) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $musicPythonWindowless)) {
    throw 'pythonw.exe is required to run the task without opening a console window.'
}
$musicTaskName = 'Chi Portfolio Spotify Refresh'
$musicAction = New-ScheduledTaskAction -Execute $musicPythonWindowless -Argument ('-B -m services.music.spotify_top --database "' + $musicDatabase + '"') -WorkingDirectory $musicSource
$musicUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$musicInterval = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(15) -RepetitionInterval (New-TimeSpan -Minutes 15)
$musicLogon = New-ScheduledTaskTrigger -AtLogOn -User $musicUser
$musicPrincipal = New-ScheduledTaskPrincipal -UserId $musicUser -LogonType Interactive -RunLevel Limited
$musicSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RunOnlyIfNetworkAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName $musicTaskName -Action $musicAction -Trigger @($musicInterval, $musicLogon) -Principal $musicPrincipal -Settings $musicSettings -Description 'Check every 15 minutes; refresh six-month Spotify top tracks when the saved ranking is at least 24 hours old.' -Force | Out-Null
Write-Output "Registered: $musicTaskName"

Write-Output "Database: $musicDatabase"
Write-Output "This task updates the local database only. Production needs its own scheduled task."
