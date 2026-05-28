# Run these in PowerShell as Administrator to register the daily task:

$Action = New-ScheduledTaskAction -Execute 'C:/Users/somay/AppData/Local/Programs/Python/Python310/python.exe' -Argument 'E:\Projects\NestShift Ltd\os-image\nestshift-os\agents\orchestrator.py --daemon'
$Trigger = New-ScheduledTaskTrigger -Daily -At 07:55am
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive
Register-ScheduledTask -TaskName "NOVA_PRIME_Agents" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force

# To remove later:
# Unregister-ScheduledTask -TaskName "NOVA_PRIME_Agents" -Confirm:$false