import asyncio
import pyttsx3
import csv
from pathlib import Path


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


_TODO_FILE = Path(__file__).resolve().with_name("todos.csv")


def _ensure_todo_file() -> None:
    if not _TODO_FILE.exists():
        # Create an empty CSV file
        _TODO_FILE.write_text("", encoding="utf-8")


def _read_todos() -> list[str]:
    _ensure_todo_file()
    items: list[str] = []
    try:
        with _TODO_FILE.open("r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                item = row[0].strip()
                if item:
                    items.append(item)
    except FileNotFoundError:
        pass
    return items


def _write_todos(items: list[str]) -> None:
    with _TODO_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for it in items:
            writer.writerow([it])
