#!/usr/bin/env bash
# Zero-publish audio master for FLOW//EXPLAIN review candidates.
# Usage: bash scripts/master_flow_explain_audio.sh INPUT.mp4 OUTPUT.mp4
set -euo pipefail
if [ "$#" -ne 2 ]; then
  echo "Usage: bash scripts/master_flow_explain_audio.sh INPUT.mp4 OUTPUT.mp4" >&2
  exit 2
fi
input="$1"
output="$2"
if [ "$input" = "$output" ] || [ ! -s "$input" ] || [ -e "$output" ]; then
  echo "Refusing missing input, same input/output, or overwrite" >&2
  exit 2
fi
for tool in ffmpeg ffprobe sha256sum; do
  command -v "$tool" >/dev/null || { echo "Missing $tool" >&2; exit 2; }
done
width="$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$input")"
height="$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$input")"
audiocodec="$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 "$input")"
if [ "$width" != "1080" ] || [ "$height" != "1920" ] || [ -z "$audiocodec" ]; then
  echo "Expected a 1080x1920 file with audio, got ${width}x${height} audio=${audiocodec}" >&2
  exit 2
fi
ffmpeg -hide_banner -loglevel error -nostdin -i "$input" \
  -map 0:v:0 -map 0:a:0 \
  -c:v copy -c:a aac -b:a 192k -af 'loudnorm=I=-18:TP=-1.5:LRA=9' \
  -movflags +faststart "$output"
ffmpeg -hide_banner -loglevel error -xerror -nostdin -i "$output" -f null -
test -s "$output"
printf "REVIEW_MASTER_PASS_NO_UPLOAD "
sha256sum "$output"
