$ErrorActionPreference='Stop'
$r='C:\Users\Dell\Desktop\youtube con'
$o=Join-Path $r 'oct18-production'
$lockPath=Join-Path $o 'oct18_single_worker.lock'
$log=Join-Path $o 'oct18_scheduled_worker.log'
$locked=$null
try {
  $locked=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
} catch {
  ('ANOTHER_WORKER_LOCKED '+(Get-Date -Format o)) |Out-File $log -Append
  exit 0
}
try {
  ('JOB_START '+(Get-Date -Format o)) |Tee-Object -FilePath $log -Append
  $v=Join-Path $r 'oct16-production\.tts-venv\Scripts\python.exe'
  $p=Join-Path $r 'flowminute-publisher-worktree\.venv\Scripts\python.exe'
  $script=Join-Path $r 'oct18-production\resumable_long_voice.py'
  $voice=Join-Path $o 'audio\long_013_natural.mp3'
  $qa=Join-Path $o 'audio\long_013_natural_qa.json'
  $model=Join-Path $r 'oct16-production\models\kokoro-v1.0.int8.onnx'
  $voices=Join-Path $r 'oct16-production\models\voices-v1.0.bin'
  & $p -m py_compile $script
  if($LASTEXITCODE -ne 0){throw 'Voice Python syntax error'}
  if(!(Test-Path $voice) -or !(Test-Path $qa)){
    'LONG013_RESUMABLE_NARRATION_START'|Tee-Object -FilePath $log -Append
    & $v -u $script --script (Join-Path $r 'flowminute-oct11\motion-v2\script-long013.txt') --output $voice --report $qa --model $model --voices $voices --voice af_heart --speed 1.09 --max-duration 370 --cache (Join-Path $o 'audio\long_013_segments') 2>&1 |Tee-Object -FilePath $log -Append
    if($LASTEXITCODE -ne 0){throw ('Long narrator exited '+$LASTEXITCODE)}
  }
  $a1=Get-Content (Join-Path $o 'audio\pilot_027_natural_qa.json') -Raw|ConvertFrom-Json
  $a2=Get-Content (Join-Path $o 'audio\pilot_028_natural_qa.json') -Raw|ConvertFrom-Json
  $a3=Get-Content $qa -Raw|ConvertFrom-Json
  if($a1.voice -ne 'af_bella' -or $a2.voice -ne 'am_michael' -or $a3.voice -ne 'af_heart') {throw 'Voice casting failed'}
  if((Get-Date) -ge (Get-Date '2026-10-18T10:45:00')){throw 'The first release is too close or in the past; do not force scheduling'}
  ('VOICE_CASTING_PASS '+$a1.voice+' '+$a2.voice+' '+$a3.voice)|Tee-Object -FilePath $log -Append
  Start-Sleep -Seconds 12
  $builder=Join-Path $r 'flowminute-oct11\scripts\oct18_build_publish.py'
  & $p -m py_compile $builder
  if($LASTEXITCODE -ne 0){throw 'Publisher Python syntax error'}
  'PIPELINE_BEGIN'|Tee-Object -FilePath $log -Append
  & $p -u $builder 2>&1|Tee-Object -FilePath $log -Append
  if($LASTEXITCODE -ne 0){throw ('Oct18 publisher exited '+$LASTEXITCODE)}
  'PUBLISHER_REPORTED_COMPLETE_AUDIT'|Tee-Object -FilePath $log -Append
  & $p (Join-Path $r 'flowminute-publisher-worktree\scripts\youtube_publisher.py') verify-queue --receipts-dir (Join-Path $r 'flowminute-oct11\state\scheduled') --date 2026-10-18 --token-file (Join-Path $r '.flowminute-private\youtube_readonly_token.json') --expected-channel-id UCCcL9Q_jqVq6LJmnYUSAFZA 2>&1|Tee-Object -FilePath $log -Append
  if($LASTEXITCODE -ne 0){throw 'Independent queue verification failed'}
  ('SUCCESS_3_OF_3_OCT18_VERIFIED '+(Get-Date -Format o))|Tee-Object -FilePath $log -Append
} catch {
  ('WORKER_STOPPED_WITH_ERROR '+(Get-Date -Format o)+' '+$_.Exception.Message)|Out-File $log -Append
  exit 1
} finally {
  if($locked){$locked.Dispose()}
}
