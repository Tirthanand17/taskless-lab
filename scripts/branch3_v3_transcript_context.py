"""Transcript evidence and context-aware proposals; no permission or viral claims.

Only unverified ASR observations. The optional CLI generates its own speech
and runs a cached Whisper model, with no external media input or network.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

MODEL = "ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66"
MAX_MS = 7_200_000
END = re.compile(r"[.!?।。！？][\"'”]?$")
CUE = re.compile(r"\b(why|how|but|instead|because|finally|mistake|unexpected|turns out)\b", re.I)


def need(ok, reason):
    if not ok:
        raise ValueError("CLIVOX_V3_TRANSCRIPT_" + reason)


def validate(rows, duration_ms):
    need(type(duration_ms) is int and 0 < duration_ms <= MAX_MS, "DURATION")
    need(type(rows) is list and len(rows) <= 12000, "ROWS")
    previous = 0
    total = 0
    for row in rows:
        need(type(row) is dict and set(row) == {"start_ms", "end_ms", "text", "words"}, "FIELDS")
        a, b, text, words = (row[k] for k in ("start_ms", "end_ms", "text", "words"))
        need(type(a) is int and type(b) is int and previous <= a < b <= duration_ms, "TIMING")
        need(type(text) is str and 0 < len(text.strip()) <= 2000 and
             not any(ord(c) < 32 and c not in "\t\n" for c in text), "TEXT")
        need(type(words) is list and len(words) <= 500, "WORDS")
        end = a
        for word in words:
            need(type(word) is dict and set(word) == {"start_ms", "end_ms", "text"}, "WORD_FIELDS")
            w, z, s = word["start_ms"], word["end_ms"], word["text"]
            need(type(w) is int and type(z) is int and end <= w < z <= b, "WORD_TIMING")
            need(type(s) is str and 0 < len(s.strip()) <= 100, "WORD_TEXT")
            end = z
        total += len(words)
        need(total <= 100000, "WORD_LIMIT")
        previous = b
    return rows


def propose_transcript(rows, duration_ms, limit=20):
    """Find complete sentence groups; cue words are weak evidence, not truth."""
    validate(rows, duration_ms)
    need(type(limit) is int and 1 <= limit <= 20, "LIMIT")
    proposals = []
    for i, first in enumerate(rows):
        if i and not END.search(rows[i-1]["text"].strip()):
            continue
        for j in range(i, min(i+25, len(rows))):
            last = rows[j]
            length = last["end_ms"] - first["start_ms"]
            if length > 55000 or (j > i and last["start_ms"]-rows[j-1]["end_ms"] > 2500):
                break
            if length < 15000 or not END.search(last["text"].strip()):
                continue
            if not first["words"] or not last["words"]:
                continue
            span = rows[i:j+1]
            if any(not r["words"] for r in span):
                continue
            speech = sum(r["end_ms"]-r["start_ms"] for r in span)
            cue = bool(CUE.search(first["text"]))
            # Integer score: local completeness, density, cue and duration only.
            score = 200 + 100*int(cue) + (100*speech)//length - abs(length-32000)//500
            proposals.append((score, i, j))
    result = []
    for score, i, j in sorted(proposals, key=lambda x: (-x[0], x[1], x[2])):
        a, b = rows[i]["start_ms"], rows[j]["end_ms"]
        if any(a < p["end_ms"] and b > p["start_ms"] for p in result):
            continue
        result.append({"start_ms": a, "end_ms": b, "semantic_event_ms": a,
                       "first_segment": i, "last_segment": j,
                       "local_editorial_priority": score,
                       "word_timing_observed": True,
                       "quote_verified": False, "human_context_required": True,
                       "render_authorized": False, "youtube_upload_authorized": False})
        if len(result) >= limit:
            break
    return result


def refine_candidate(candidate, rows, duration_ms):
    """Refine a numeric proposal only when a complete transcript span contains its anchor."""
    validate(rows, duration_ms)
    a, b, t = (candidate.get(k) for k in ("start_ms", "end_ms", "anchor_ms"))
    need(all(type(x) is int for x in (a,b,t)) and 0 <= a <= t < b <= duration_ms, "CANDIDATE")
    options = [p for p in propose_transcript(rows, duration_ms)
               if p["start_ms"] <= t < p["end_ms"]
               and abs(p["start_ms"]-a) <= 10000 and abs(p["end_ms"]-b) <= 10000]
    if not options:
        return None
    return min(options, key=lambda p: (abs(p["start_ms"]-a)+abs(p["end_ms"]-b),
                                      -p["local_editorial_priority"]))


def fixture_rows():
    out = []
    for offset, lines in [(0, ["Why does the first move matter?", "The player waits before turning.",
                                "But the opponent moves too early.", "That is why the setup works."]),
                          (50000, ["How can we read the result?", "The frame contains a clear clue.",
                                   "Finally the movement reveals the answer.", "The explanation is complete."])]:
        for i, line in enumerate(lines):
            a = offset+i*6000
            words = line.split()
            out.append({"start_ms": a, "end_ms": a+6000, "text": line,
                        "words": [{"start_ms": a+k*6000//len(words),
                                   "end_ms": a+(k+1)*6000//len(words), "text": w}
                                  for k,w in enumerate(words)]})
    return out


def generated_speech_smoke():
    """Use only generated speech, offline cached model; no new model download."""
    from faster_whisper import WhisperModel
    from huggingface_hub import snapshot_download
    import os
    sentence = ("Why does a microphone sound different across the room? "
                "The microphone records your voice and the reflections from the walls. "
                "Move closer and the balance changes before you touch a single setting. "
                "Try the same sentence twice and listen to the difference. "
                "The quieter room often matters more than an expensive microphone. "
                "That simple comparison is a good place to start.")
    with tempfile.TemporaryDirectory(prefix="clivox-v3-asr-") as d:
        wav = Path(d)/"generated.wav"
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        if exe:
            subprocess.run([exe, "-v", "en", "-s", "145", "-w", str(wav), sentence], check=True, timeout=60)
        elif os.name == "nt":
            cmd = ("Add-Type -AssemblyName System.Speech; "
                   "$v=New-Object System.Speech.Synthesis.SpeechSynthesizer; $v.Rate=-2; "
                   "$v.SetOutputToWaveFile($env:CLIVOX_TEST_WAV); "
                   "$v.Speak($env:CLIVOX_TEST_TEXT); $v.Dispose()")
            subprocess.run(["powershell.exe","-NoProfile","-Command",cmd], check=True, timeout=60,
                           env={**os.environ,"CLIVOX_TEST_WAV":str(wav),"CLIVOX_TEST_TEXT":sentence})
        else:
            raise RuntimeError("No local speech synthesizer")
        with wave.open(str(wav)) as f:
            duration = math.ceil(f.getnframes()*1000/f.getframerate())
        weights = snapshot_download("Systran/faster-whisper-base", revision=MODEL, local_files_only=True)
        model = WhisperModel(weights,device="cpu",compute_type="int8",cpu_threads=4,local_files_only=True)
        segments, _ = model.transcribe(str(wav), language="en", vad_filter=True, beam_size=3, word_timestamps=True)
        rows, previous = [], 0
        for s in segments:
            a,b = max(previous,round(s.start*1000)), min(duration,round(s.end*1000))
            if a >= b or not s.text.strip():
                continue
            words, end = [], a
            for w in s.words or []:
                u,v = max(end,round(w.start*1000)),min(b,round(w.end*1000))
                if u < v and w.word.strip():
                    words.append({"start_ms":u,"end_ms":v,"text":w.word.strip()})
                    end = v
            rows.append({"start_ms":a,"end_ms":b,"text":s.text.strip(),"words":words})
            previous=b
        choices=propose_transcript(rows,duration)
        need(bool(rows and choices),"GENERATED_ASR_NO_PROPOSAL")
        return {"generated_speech_only":True,"asr":"faster-whisper-base-int8",
                "duration_ms":duration,"segments":len(rows),"words":sum(len(r["words"]) for r in rows),
                "proposals":len(choices),"production_ready":False,"youtube_upload_authorized":False}



def combine_observations(measurements, rows):
    """Recompute source-free semantic anchors and refine without losing event evidence."""
    import hashlib
    from scripts.branch3_v3_multimodal_candidates import validate as validate_features, propose, canonical
    validate_features(measurements)
    need(measurements["semantic_events_ms"] is None, "SEMANTIC_MUST_BE_RECOMPUTED")
    duration = measurements["duration_ms"]
    semantic = propose_transcript(rows, duration)
    doc = dict(measurements, semantic_events_ms=sorted({p["semantic_event_ms"] for p in semantic}))
    report = propose(doc)
    selected, rejected = [], 0
    for candidate in report["candidates"]:
        refined = refine_candidate(candidate, rows, duration)
        item = dict(candidate)
        if refined is not None and all(refined["start_ms"] <= e["time_ms"] < refined["end_ms"]
                                      for e in candidate["evidence"]):
            item.update(start_ms=refined["start_ms"], end_ms=refined["end_ms"],
                        transcript_segment_range=[refined["first_segment"], refined["last_segment"]],
                        context_state="UNVERIFIED_TRANSCRIPT_BOUNDARIES")
        elif doc["profile"] == "dialogue":
            rejected += 1
            continue
        else:
            item.update(transcript_segment_range=None, context_state="HUMAN_CONTEXT_REQUIRED")
        if any(item["start_ms"] < c["end_ms"] and item["end_ms"] > c["start_ms"] for c in selected):
            rejected += 1
            continue
        item["quote_verified"] = False
        selected.append(item)
    return {"stage":"V3_UNAPPROVED_COMBINED_CANDIDATES",
            "transcript_observation_digest_not_media_or_rights":hashlib.sha256(canonical(rows)).hexdigest(),
            "measurement_digest":report["measurement_sha256_not_media_or_license"],
            "semantic_proposal_count":len(semantic), "rejected_context_or_overlap":rejected,
            "candidates":selected, "creator_rights_verified":False,
            "human_editor_approved":False, "ready_to_render":False,
            "youtube_upload_authorized":False, "viral_probability":None}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-speech",action="store_true")
    args=parser.parse_args()
    if args.generated_speech:
        print(json.dumps(generated_speech_smoke(),sort_keys=True))
    else:
        print(json.dumps({"fixture_only":True,"proposals":propose_transcript(fixture_rows(),80000)},sort_keys=True))
