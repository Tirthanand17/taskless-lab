# Automatically resumes a stopped, checkpointed Oct18 job.
# Does not call YouTube API or create duplicate uploads. Main worker uses an exclusive lock and an immutable upload ledger.
$ErrorActionPreference='Stop'
$root='C:\Users\Dell\Desktop\youtube con'
$dir=Join-Path $root 'oct18-production'
$log=Join-Path $dir 'oct18_scheduled_worker.log'
if((Get-Date) -ge (Get-Date '2026-10-18T10:30:00')){exit 0}
if(Test-Path $log){
  if(Select-String -Path $log -Pattern 'SUCCESS_3_OF_3_OCT18_VERIFIED' -Quiet){exit 0}
}
$task=Get-ScheduledTask -TaskName 'FlowMinuteOct18Production' -ErrorAction Stop
if($task.State -eq 'Running'){exit 0}
$now=Get-Date -Format o
("WATCHDOG_RESUME "+$now+" previous_state="+$task.State) |Out-File $log -Append -Encoding utf8
Start-ScheduledTask -TaskName 'FlowMinuteOct18Production'
