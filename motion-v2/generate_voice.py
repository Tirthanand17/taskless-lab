from pathlib import Path
import asyncio
import edge_tts

ROOT = Path(__file__).resolve().parent
text = (ROOT / "script.txt").read_text(encoding="utf-8").strip()
out = ROOT / "public" / "voice.mp3"
out.parent.mkdir(parents=True, exist_ok=True)

async def main():
    communicate = edge_tts.Communicate(
        text=text,
        voice="en-US-ChristopherNeural",
        rate="+4%",
        pitch="+0Hz",
        volume="+0%"
    )
    await communicate.save(str(out))

asyncio.run(main())
print(out)
