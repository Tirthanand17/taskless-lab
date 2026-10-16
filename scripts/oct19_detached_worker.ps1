$ErrorActionPreference='Stop'
$r='C:\Users\Dell\Desktop\youtube con'
$o=Join-Path $r 'oct19-production'
New-Item -ItemType Directory -Path (Join-Path $o 'audio') -Force|Out-Null
$log=Join-Path $o 'oct19_scheduled_worker.log'
$lockFile=Join-Path $o 'oct19_single_worker.lock'
$held=$null
try {$held=[IO.File]::Open($lockFile,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}
catch {('LOCK_HELD '+(Get-Date -Format o))|Out-File $log -Append;exit 0}
try{
 ('START_OCT19 '+(Get-Date -Format o))|Tee-Object -FilePath $log -Append
 $tts=Join-Path $r 'oct16-production\.tts-venv\Scripts\python.exe'
 $py=Join-Path $r 'flowminute-publisher-worktree\.venv\Scripts\python.exe'
 $voiceScript=Join-Path $r 'flowminute-oct11\scripts\oct18_resumable_long_voice.py'
 $model=Join-Path $r 'oct16-production\models\kokoro-v1.0.int8.onnx'
 $voices=Join-Path $r 'oct16-production\models\voices-v1.0.bin'
 $jobs=@(
 @('pilot_029','script-v29.txt','af_nicole','1.08','60'),
 @('pilot_030','script-v30.txt','am_adam','1.09','60'),
 @('long_014','script-long014.txt','af_heart','1.10','430')
 )
 foreach($v in $jobs) {
  $ep=$v[0];$voice=$v[2]
  $mp3=Join-Path $o ('audio\'+$ep+'_natural.mp3')
  $qa=Join-Path $o ('audio\'+$ep+'_natural_qa.json')
  if((Test-Path $mp3) -and (Test-Path $qa) -and (Get-Item $mp3).Length -gt 16000) {
    $q=Get-Content $qa -Raw|ConvertFrom-Json
    if($q.voice -ne $voice){throw ('VOICE_MISMATCH '+$ep)}
    ('REUSED '+$ep+' voice='+$voice+' secs='+$q.audio_duration_seconds)|Tee-Object -FilePath $log -Append
  } else {
    ('VOICE_BEGIN '+$ep+' voice='+$voice+' '+(Get-Date -Format o))|Tee-Object -FilePath $log -Append
    & $tts -u $voiceScript --script (Join-Path $r ('flowminute-oct11\motion-v2\'+$v[1])) --output $mp3 --report $qa --model $model --voices $voices --voice $voice --speed $v[3] --max-duration $v[4] --cache (Join-Path $o ('audio\'+$ep+'_segments')) 2>&1 |Tee-Object -FilePath $log -Append
    if($LASTEXITCODE -ne 0){throw ('VOICE_ERROR '+$ep+' '+$LASTEXITCODE)}
    ('VOICE_DONE '+$ep+' '+(Get-Date -Format o))|Tee-Object -FilePath $log -Append
  }
 }
 $q1=Get-Content (Join-Path $o 'audio\pilot_029_natural_qa.json') -Raw|ConvertFrom-Json
 $q2=Get-Content (Join-Path $o 'audio\pilot_030_natural_qa.json') -Raw|ConvertFrom-Json
 $q3=Get-Content (Join-Path $o 'audio\long_014_natural_qa.json') -Raw|ConvertFrom-Json
 if($q1.voice -ne 'af_nicole' -or $q2.voice -ne 'am_adam' -or $q3.voice -ne 'af_heart'){throw 'VOICE_CASTING_INVALID'}
 if($q1.voice -eq $q2.voice){throw 'SHORTS_REQUIRE_DISTINCT_VOICES'}
 ('VOICE_DISTINCT_QA_PASS '+$q1.voice+' '+$q2.voice+' '+$q3.voice)|Tee-Object -FilePath $log -Append
 if((Get-Date) -ge (Get-Date '2026-10-19T10:30:00')){throw 'TOO_LATE_FIRST_RELEASE_FAIL_CLOSED'}
 $build=Join-Path $r 'flowminute-oct11\scripts\oct19_build_publish.py'
 & $py -m py_compile $build
 if($LASTEXITCODE -ne 0){throw 'PUBLISHER_CODE_SYNTAX_FAILED'}
 ('RENDER_QA_UPLOAD_BEGIN '+(Get-Date -Format o))|Tee-Object -FilePath $log -Append
 & $py -u $build 2>&1 |Tee-Object -FilePath $log -Append
 if($LASTEXITCODE -ne 0){throw ('PIPELINE_FAILED '+$LASTEXITCODE)}
 ('INDEPENDENT_YOUTUBE_AUDIT '+(Get-Date -Format o))|Tee-Object -FilePath $log -Append
 & $py (Join-Path $r 'flowminute-publisher-worktree\scripts\youtube_publisher.py') verify-queue --receipts-dir (Join-Path $r 'flowminute-oct11\state\scheduled') --date 2026-10-19 --token-file (Join-Path $r '.flowminute-private\youtube_readonly_token.json') --expected-channel-id UCCcL9Q_jqVq6LJmnYUSAFZA 2>&1|Tee-Object -FilePath $log -Append
 if($LASTEXITCODE -ne 0){throw ('INDEPENDENT_YOUTUBE_AUDIT_FAILED '+$LASTEXITCODE)}
 ('SUCCESS_3_OF_3_OCT19_VERIFIED '+(Get-Date -Format o))|Tee-Object -FilePath $log -Append
} catch {
 ('JOB_STOPPED_WITH_ERROR '+(Get-Date -Format o)+' '+$_.Exception.Message)|Out-File $log -Append
 exit 1
} finally {
 if($held){$held.Dispose()}
}
