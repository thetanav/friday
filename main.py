import asyncio
import sys
from collections import deque
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

    print(">>> Listening Active... (Ctrl+C to stop)")
    # Keep a short rolling history of prior exchanges for context
    history: deque[tuple[str, str]] = deque(maxlen=10)  # (user, friday)
    while True:
        try:
            try:
                user_text = await recognize_speech_once()
            except EOFError:
                break

            if not user_text:
                await asyncio.sleep(0.1)
                continue

            print(">>>", user_text)
            # Build a compact prompt that includes recent conversation for context
            if history:
                convo = "\n".join(f"User: {u}\nFriday: {a}" for u, a in history)
            else:
                convo = "(no prior context)"

            # Trim context to a safe size (defensive against very long turns)
            if len(convo) > 4000:
                convo = convo[-4000:]

            contextual_prompt = (
                "You are in an ongoing conversation.\n"
                "Conversation so far:\n"
                f"{convo}\n\n"
                f"Current user message: {user_text}\n"
                "Respond as Friday, concise and helpful."
            )

            # Await the async agent call with contextual prompt
            result = await agent.run(contextual_prompt)
            friday_response = result.output.text
            print("    Friday:", friday_response)
            await tts(friday_response)

            # Update history
            history.append((user_text, friday_response))

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
