"""FlowMinute voice entry point: natural delivery by default for all NEW episodes.

The older one-shot Edge TTS engine is still available explicitly with --style legacy.
Old historical workflows must pass --style legacy to remain reproducible.
"""
from pathlib import Path
import argparse
import asyncio
import edge_tts
import natural_narration

ROOT = Path(__file__).resolve().parent


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--script", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--voice", default=None)
    p.add_argument("--rate", default=None, help="Only valid with --style legacy")
    p.add_argument("--style", choices=["natural", "legacy"], default="natural")
    p.add_argument("--preset", choices=tuple(natural_narration.VOICE_PRESETS),
                   default="warm-explainer")
    p.add_argument("--report", default=None)
    p.add_argument("--max-duration", type=float, default=None)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


async def legacy_generate(text, out: Path, *, voice: str, rate: str):
    service = edge_tts.Communicate(
        text=text, voice=voice, rate=rate, pitch="+0Hz", volume="+0%"
    )
    await service.save(str(out))


def main():
    args = parse_args()
    script = (ROOT / args.script).resolve()
    out = (ROOT / "public" / args.output).resolve()
    if args.style == "natural":
        if args.rate is not None:
            raise SystemExit("--rate only applies to --style legacy; natural mode uses subtle segment pacing")
        cli = ["--script", str(script), "--output", str(out),
               "--preset", args.preset]
        if args.voice:
            cli += ["--voice", args.voice]
        if args.report:
            cli += ["--report", str((ROOT / args.report).resolve())]
        if args.max_duration is not None:
            cli += ["--max-duration", str(args.max_duration)]
        if args.dry_run:
            cli += ["--dry-run"]
        return natural_narration.main(cli)

    if args.dry_run:
        raise SystemExit("--dry-run is only supported in natural style")
    if args.report:
        raise SystemExit("--report is only supported in natural style")
    text = script.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit("Script is empty")
    out.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(legacy_generate(text, out, voice=args.voice or "en-US-AvaNeural",
                                rate=args.rate or "+3%"))
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
