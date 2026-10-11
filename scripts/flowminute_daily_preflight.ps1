<#
.SYNOPSIS
  FlowMinute Lab's safe, read-only YouTube schedule preflight.
.DESCRIPTION
  Never uploads, publishes, reschedules, edits metadata, or retrieves secret token values.
  Exits nonzero on any discrepancy. Works with the installed Windows Python virtual env.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\flowminute_daily_preflight.ps1 -Date 2026-10-12
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$Date,
  [string]$ChannelId = "UCCcL9Q_jqVq6LJmnYUSAFZA"
)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $project '.venv\Scripts\python.exe'
$publisher = Join-Path $project 'scripts\youtube_publisher.py'
$token = Join-Path $HOME '.flowminute-private\youtube_readonly_token.json'
if (!(Test-Path $python)) {throw "Local Python env missing: $python"}
if (!(Test-Path $token)) {throw "Read-only OAuth token missing. Complete OAuth setup first."}
Write-Output "FlowMinute Daily Preflight for $Date (READ ONLY)"
& $python $publisher auth-health --token-file $token --mode read
if ($LASTEXITCODE -ne 0) {throw "OAuth health check failed; preflight stopped"}
& $python $publisher verify-queue --date $Date --token-file $token --expected-channel-id $ChannelId
if ($LASTEXITCODE -ne 0) {throw "Scheduled video mismatch or OAuth failure; inspect Studio"}
Write-Output "PASS: no scheduled queue discrepancies detected. No YouTube changes made."
