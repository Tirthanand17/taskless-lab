from pathlib import Path
import argparse
import asyncio
import edge_tts

ROOT = Path(__file__).resolve().parent

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--script", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--voice", default="en-US-AvaNeural")
    p.add_argument("--rate", default="+3%")
    return p.parse_args()

async def main():
    args = parse_args()
    text = (ROOT / args.script).read_text(encoding="utf-8").strip()
    out = ROOT / "public" / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(
        text=text,
        voice=args.voice,
        rate=args.rate,
        pitch="+0Hz",
        volume="+0%"
    )
    await communicate.save(str(out))
    print(out)

asyncio.run(main())
