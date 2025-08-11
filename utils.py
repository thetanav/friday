import asyncio
import pyttsx3


def _tts_blocking(text: str) -> None:
    """Blocking TTS using pyttsx3."""
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[1].id)
    engine.setProperty("rate", 180)
    engine.setProperty("volume", 0.9)
    engine.say(text)

    engine.runAndWait()


async def tts(text: str) -> None:
    """Run TTS in a worker thread to avoid blocking the asyncio loop."""
    if not text:
        return
    await asyncio.to_thread(_tts_blocking, text)
