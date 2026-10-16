$ErrorActionPreference='Stop'
$root='C:\Users\Dell\Desktop\youtube con'
$dir=Join-Path $root 'oct19-production'
$log=Join-Path $dir 'oct19_scheduled_worker.log'
if((Get-Date) -ge (Get-Date '2026-10-19T10:30:00')){exit 0}
if(Test-Path $log){
 if(Select-String -Path $log -Pattern 'SUCCESS_3_OF_3_OCT19_VERIFIED' -Quiet){exit 0}
}
$task=Get-ScheduledTask -TaskName FlowMinuteOct19Production -ErrorAction Stop
if($task.State -eq 'Running'){exit 0}
('WATCHDOG_RESTART '+(Get-Date -Format o))|Out-File $log -Append -Encoding utf8
Start-ScheduledTask -TaskName FlowMinuteOct19Production
