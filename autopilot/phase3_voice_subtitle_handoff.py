"""Phase 3R1/3R4: script-derived subtitle timings and WAV voice *intake*.

No downloaded voices, voice cloning, third-party service, camera/device input,
or publishing. Text cue timings are ESTIMATED from screenplay slots, not aligned
against recognized speech. An externally supplied WAV is technical audio only:
a waveform cannot prove identity, licensing, language or natural human speech.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import math
import re
import wave

from .agent_org import WorkflowError
from .phase2r3_authored_pack_audit import SOURCE, SECTIONS, HEADERS, TIME, _sections, _seconds

MAX_CUE_CHARS = 90
MAX_CUE_DURATION_MS = 6000
MAX_VOICE_BYTES = 70 * 1024 * 1024
IDENTIFIER = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")


@dataclass(frozen=True)
class SubtitleCue:
    start_ms: int
    end_ms: int
    text: str


def _timecode(milliseconds: int) -> str:
    if type(milliseconds) is not int or milliseconds < 0 or milliseconds > 3_600_000:
        raise WorkflowError("Invalid subtitle timecode")
    h, rem = divmod(milliseconds, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _chunks(text: str, duration_ms: int) -> list[str]:
    """Sentence-preserving best-effort split with bounded display length."""
    if not isinstance(text,str) or "\n" in text or "\r" in text or "<" in text or ">" in text:
        raise WorkflowError("Only safe one-line screenplay text accepted")
    words = text.split()
    if not words or any(len(word) > MAX_CUE_CHARS for word in words):
        raise WorkflowError("Invalid or oversized single subtitle word")
    # Keep per-cue time reasonable, and avoid tiny last cue by allocating words
    # across a number of estimated intervals; no claim of real phoneme timing.
    min_chunks = math.ceil(duration_ms/MAX_CUE_DURATION_MS)
    n = max(min_chunks, math.ceil(len(text)/MAX_CUE_CHARS))
    if n > len(words) or n > 20:
        raise WorkflowError("Insufficient words for readable timed cues")
    # Group contiguous words into near-even *character* weights.
    result=[]
    pos=0
    for group in range(n):
        remaining=n-group
        remaining_words=len(words)-pos
        if remaining_words < remaining:
            raise WorkflowError("Insufficient words to divide cues")
        if group==n-1:
            end=len(words)
        else:
            available=sum(len(w)+1 for w in words[pos:])
            target=available/remaining
            count=0
            end=pos
            while end<len(words)-(remaining-1):
                next_count=count+len(words[end])+(1 if end>pos else 0)
                if end>pos and (next_count>target or next_count>MAX_CUE_CHARS):
                    break
                count=next_count
                end+=1
            end=max(end,pos+1)
        part=" ".join(words[pos:end])
        if len(part)>MAX_CUE_CHARS:
            raise WorkflowError("Timed caption exceeds display-safe length")
        result.append(part)
        pos=end
    if " ".join(result)!=" ".join(words):
        raise WorkflowError("Subtitle split unexpectedly changed the spoken text")
    return result


def build_subtitles_from_authored_csv(*, markdown: str | None = None) -> dict:
    """Generate SRT and metadata for all three *draft* scripts, no I/O writes.

    Output strings contain original voice lines; do not log them into public
    CI. The returned SRT is not proof of spoken timing, intelligibility or rights.
    """
    raw=SOURCE.read_text(encoding="utf-8") if markdown is None else markdown
    sections=_sections(raw)
    output={}
    for section,(kind,language,episode,narrator,expected_seconds,beat_count) in zip(sections,SECTIONS):
        rows=TIME.findall(section)
        if len(rows)!=beat_count:
            raise WorkflowError("Unexpected authored voice segment count")
        cues=[]
        last=0
        for a,b,c,d,spoken,_visual in rows:
            start=_seconds(a,b)*1000
            end=_seconds(c,d)*1000
            if start!=last or end<=start:
                raise WorkflowError("Subtitle scene gap or overlap")
            last=end
            fragments=_chunks(spoken,end-start)
            span=end-start
            n=len(fragments)
            for i,line in enumerate(fragments):
                cue_start=start+(span*i)//n
                cue_end=start+(span*(i+1))//n
                if cue_end-cue_start>MAX_CUE_DURATION_MS:
                    raise WorkflowError("Readable caption interval too long")
                cues.append(SubtitleCue(cue_start,cue_end,line))
        if last!=expected_seconds*1000:
            raise WorkflowError("Author's script duration differs from subtitle plan")
        if any(cues[i].start_ms!=cues[i-1].end_ms for i in range(1,len(cues))):
            raise WorkflowError("Rendered captions are not contiguous")
        srt="\n".join(
            f"{i}\n{_timecode(cue.start_ms)} --> {_timecode(cue.end_ms)}\n{cue.text}\n"
            for i,cue in enumerate(cues,1)
        )+"\n"
        output[episode]={
            "kind":kind,"language":language,"narrator_plan_id":narrator,
            "duration_ms":last,"cue_count":len(cues),
            "script_sha256":sha256(" ".join(row[4] for row in rows).encode("utf-8")).hexdigest(),
            "srt_sha256":sha256(srt.encode("utf-8")).hexdigest(),
            "srt":srt,
            "timings_are_script_estimates":True,
            "actual_voice_alignment_verified":False,
            "actual_narration_present":False,
            "ready_for_upload":False,
        }
    if len(output)!=3:
        raise WorkflowError("Exactly three draft subtitle files required")
    return output


def export_subtitle_files(destination: Path) -> dict:
    """Explicit local file export ONLY, never implicitly used by CI or upload."""
    output=build_subtitles_from_authored_csv()
    folder=Path(destination)
    if folder.is_symlink() or not folder.is_dir():
        raise WorkflowError("Destination must already be an ordinary directory")
    summaries={}
    for episode,record in sorted(output.items()):
        target=folder/(episode+".draft_estimated.srt")
        if target.is_symlink() or target.exists():
            raise WorkflowError("Refusing to overwrite any existing caption asset")
        # No network, subprocess, published video or outside file reads.
        target.write_text(record["srt"],encoding="utf-8",newline="\n")
        summaries[episode]={
            key:value for key,value in record.items() if key!="srt"
        }
    return summaries


def inspect_external_voice_wav(
    path: Path, *, episode_id: str, expected_seconds: float,
    declared_narrator_id: str, declared_language: str,
) -> dict:
    """Bounded actual PCM WAV inspection; never a voice/rights attestation.

    Rejects raw silence/near silence and duration/channel/sample-rate errors.
    A synthetic sine wave can still satisfy amplitude/frequency tests, so this
    result is always ONLY "WAV_TECHNICAL_EVIDENCE_NOT_SPEECH_APPROVAL".
    """
    if (not isinstance(episode_id,str) or not IDENTIFIER.fullmatch(episode_id)
            or not isinstance(declared_narrator_id,str)
            or not re.fullmatch(r"narrator_[a-z0-9_]{2,30}",declared_narrator_id)
            or declared_language not in ("en","hi")
            or not isinstance(expected_seconds,(int,float))
            or isinstance(expected_seconds,bool)
            or not math.isfinite(expected_seconds)
            or not 0.25 <= expected_seconds <= 600):
        raise WorkflowError("Invalid bounded claimed voice metadata")
    f=Path(path)
    if not f.is_file() or f.is_symlink() or f.suffix.lower()!=".wav":
        raise WorkflowError("Plain local WAV file required")
    size=f.stat().st_size
    if not 44 <= size <= MAX_VOICE_BYTES:
        raise WorkflowError("Voice WAV exceeds permitted file bounds")
    try:
        with wave.open(str(f),"rb") as reader:
            channels=reader.getnchannels()
            rate=reader.getframerate()
            width=reader.getsampwidth()
            samples=reader.getnframes()
            compression=reader.getcomptype()
            if (channels not in (1,2) or rate not in (16000,22050,24000,44100,48000)
                    or width!=2 or compression!="NONE"
                    or not 0.25<=samples/rate<=600
                    or abs(samples/rate-expected_seconds)>1.5):
                raise WorkflowError("Voice waveform properties or duration inconsistent")
            import audioop
            checked=0
            peak=0
            rms_sum=0.0
            # Loop bounded by file size, no buffering huge recordings in memory.
            while True:
                chunk=reader.readframes(4096)
                if not chunk:
                    break
                checked+=len(chunk)
                peak=max(peak,audioop.max(chunk,2))
                rms=audioop.rms(chunk,2)/32768
                rms_sum+=rms*rms*(len(chunk)//(2*channels))
            if checked==0 or peak==0:
                raise WorkflowError("Silent WAV is not a narrator")
            root_mean=math.sqrt(rms_sum/samples)
            if not 0.004 <= root_mean <= 0.9:
                raise WorkflowError("Voice input energy outside expected level")
    except (wave.Error,EOFError,OSError) as exc:
        raise WorkflowError("WAV read or decoding failed") from exc
    file_hash=sha256()
    with f.open("rb") as stream:
        for data in iter(lambda: stream.read(1024*1024),b""):
            file_hash.update(data)
    return {
        "status":"WAV_TECHNICAL_EVIDENCE_NOT_SPEECH_APPROVAL",
        "episode_id":episode_id,
        "sha256":file_hash.hexdigest(),
        "duration_seconds":round(samples/rate,4),
        "declared_language":declared_language,
        "declared_narrator_id":declared_narrator_id,
        "channels":channels,"sample_rate":rate,"peak_normalized":round(peak/32768,4),
        "rms_normalized":round(root_mean,5),
        "real_speech_verified":False,
        "human_naturalness_verified":False,
        "language_pronunciation_verified":False,
        "narrator_identity_verified":False,
        "license_rights_verified":False,
        "audio_caption_alignment_verified":False,
        "publishable":False,
        "network_calls":0,
    }
