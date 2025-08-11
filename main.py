import os
import asyncio
import sys
from utils import tts
import speech_recognition as sr
from agent import agent


running = True  # Global flag to control the main loop (kept for compatibility)


r = sr.Recognizer()


async def recognize_speech_once() -> str | None:
    """Capture a single utterance using SpeechRecognition in a thread."""

    def _recognize_blocking() -> str | None:
        with sr.Microphone() as source:
            try:
                r.adjust_for_ambient_noise(source, duration=0.3)
            except Exception:
                # Ambient noise adjustment is best-effort
                pass
            audio = r.listen(source)
        try:
            return r.recognize_google(audio)
        except sr.UnknownValueError:
            print(">>> Friday: Sorry, I didn't catch that.")
            return None
        except sr.RequestError as e:
            print(f">>> Friday: Speech recognition service error: {e}")
            return None

    try:
        return await asyncio.to_thread(_recognize_blocking)
    except OSError as e:
        # Microphone may not be available
        print(f">>> Friday: Microphone error: {e}")
        return None


async def run_loop():
    """Main loop using a single long-lived asyncio event loop."""

    # Optional modes for easier testing or environments without mic
    text_mode = os.environ.get("FRIDAY_TEXT_MODE") == "1"
    oneshot_text = os.environ.get("FRIDAY_ONESHOT_TEXT")

    if oneshot_text:
        print(">>>", oneshot_text)
        result = await agent.run(oneshot_text)
        friday_response = result.output.text
        print("    Friday:", friday_response)
        await tts(friday_response)
        return

    print(">>> Listening Active... (Ctrl+C to stop)")
    while True:
        try:
            if text_mode:
                try:
                    user_text = await asyncio.to_thread(input, ">>> ")
                except EOFError:
                    break
            else:
                user_text = await recognize_speech_once()

            if not user_text:
                await asyncio.sleep(0.1)
                continue

            print(">>>", user_text)
            # Await the async agent call
            result = await agent.run(user_text)
            friday_response = result.output.text
            print("    Friday:", friday_response)
            await tts(friday_response)

            await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\n>>> Shutting down...")
            break
        except Exception as e:
            # Keep the loop alive on transient errors
            print(f">>> Friday: Error occurred: {e}")
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    # Prefer selector event loop on Windows to avoid Proactor quirks with threads
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

    # Single, long-lived loop
    asyncio.run(run_loop())
