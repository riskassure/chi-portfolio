# Run locally to register this user's Spotify refresh task. No password is stored.
$ErrorActionPreference = 'Stop'
$musicSource = Join-Path $PSScriptRoot 'src'
$musicPython = (Get-Command python.exe).Source
$musicPythonWindowless = Join-Path (Split-Path $musicPython) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $musicPythonWindowless)) {
    throw 'pythonw.exe is required to run the task without opening a console window.'
}
$musicTaskName = 'Chi Portfolio Spotify Refresh'
$musicAction = New-ScheduledTaskAction -Execute $musicPythonWindowless -Argument '-B -m services.music.spotify_jobs' -WorkingDirectory $musicSource
$musicUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$musicInterval = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(15) -RepetitionInterval (New-TimeSpan -Minutes 15)
$musicLogon = New-ScheduledTaskTrigger -AtLogOn -User $musicUser
$musicPrincipal = New-ScheduledTaskPrincipal -UserId $musicUser -LogonType Interactive -RunLevel Limited
$musicSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RunOnlyIfNetworkAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName $musicTaskName -Action $musicAction -Trigger @($musicInterval, $musicLogon) -Principal $musicPrincipal -Settings $musicSettings -Description 'Collect Spotify activity every 15 minutes; refresh the local ranked music catalog when seven days have elapsed.' -Force | Out-Null
Write-Output "Registered: $musicTaskName"
