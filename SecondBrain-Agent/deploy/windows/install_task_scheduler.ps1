$Action = New-ScheduledTaskAction -Execute "python" -Argument "H:\SecondBrainAgent\SecondBrain-Agent\scripts\scheduler.py" -WorkingDirectory "H:\SecondBrainAgent\SecondBrain-Agent"
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "SecondBrain-Agent" -Action $Action -Trigger $Trigger -Settings $Settings -Description "SecondBrain-Agent Scheduler"
Write-Host "Task Scheduler Eintrag erstellt: SecondBrain-Agent"
