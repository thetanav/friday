import asyncio
import sys
from collections import deque
from utils import tts
import speech_recognition as sr
from agent import agent
from rich.console import Console
from rich.panel import Panel
from rich import box
import typer


running = True  # Global flag to control the main loop (kept for compatibility)
console = Console()
app = typer.Typer(help="Friday CLI")


r = sr.Recognizer()


async def recognize_speech_once() -> str | None:
    """Capture a single utterance using SpeechRecognition in a thread."""

    def _recognize_blocking() -> str | None:
        with sr.Microphone() as source:
            try:
                r.adjust_for_ambient_noise(source, duration=0.3)
            except Exception:
                pass
            audio = r.listen(source)
        try:
            return r.recognize_google(audio)
        except sr.RequestError as e:
            console.print(
                Panel(
                    f"Speech recognition service error:\n{e}",
                    title="Friday",
                    border_style="red",
                    box=box.ROUNDED,
                )
            )
            return None

    try:
        return await asyncio.to_thread(_recognize_blocking)
    except OSError as e:
        # Microphone may not be available
        console.print(
            Panel(
                f"Microphone error:\n{e}",
                title="Friday",
                border_style="red",
                box=box.ROUNDED,
            )
        )
        return None


async def run_loop():
    """Main loop using a single long-lived asyncio event loop."""

    console.print(
        Panel(
            "Listening Active… (Ctrl+C to stop)",
            title="Friday Listen",
            border_style="green",
            box=box.ROUNDED,
        )
    )
    # Keep a short rolling history of prior exchanges for context
    history: deque[tuple[str, str]] = deque(maxlen=10)  # (user, friday)
    while True:
        try:
            try:
                with console.status("Listening...", spinner="dots"):
                    user_text = await recognize_speech_once()
            except EOFError:
                break

            if not user_text:
                await asyncio.sleep(0.2)
                continue

            # Show user's recognized text
            console.print(f"[bold cyan]You[/]  {user_text}")

            # Quick quit by voice hints
            low = user_text.strip().lower()
            if low in {"q", "quit", "exit", "stop", "goodbye"}:
                console.print("[dim]Bye.[/]")
                break
            # Build a compact prompt that includes recent conversation for context
            if history:
                convo = "\n".join(f"User: {u}\nFriday: {a}" for u, a in history)
            else:
                convo = "(no prior context)"

            # Trim context to a safe size (defensive against very long turns)
            if len(convo) > 1000:
                convo = convo[-1000:]

            contextual_prompt = (
                "You are in an ongoing conversation.\n"
                "Conversation so far:\n"
                f"{convo}\n\n"
                f"Current user message: {user_text}\n"
                "Respond as Friday, concise and helpful."
            )

            with console.status("Thinking...", spinner="dots"):
                result = await agent.run(contextual_prompt)
            friday_response = result.output.text
            await tts(friday_response)
            console.print(
                Panel.fit(
                    friday_response,
                    title="Friday",
                    border_style="cyan",
                    box=box.ROUNDED,
                )
            )

            # Update history
            history.append((user_text, friday_response))
        except asyncio.CancelledError:
            console.print("\n[dim]Shutting down…[/]")
            break
        except KeyboardInterrupt:
            console.print("\n[dim]Shutting down…[/]")
            break
        except Exception as e:
            # Keep the loop alive on transient errors
            console.print(
                Panel(
                    f"Error occurred:\n{e}",
                    title="Friday",
                    border_style="red",
                    box=box.ROUNDED,
                )
            )
            await asyncio.sleep(0.5)


def _windows_loop_patch():
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass


def _suppress_keyboard_interrupt_traceback():
    """Silence the noisy traceback/aborted message on Ctrl+C for a clean exit."""
    default_hook = sys.excepthook

    def _quiet_hook(exc_type, exc, tb):
        if exc_type is KeyboardInterrupt:
            # Quietly exit; no traceback, no extra noise
            return
        return default_hook(exc_type, exc, tb)

    sys.excepthook = _quiet_hook


if __name__ == "__main__":
    # Backward-compatible default: no args -> listen, else CLI
    _suppress_keyboard_interrupt_traceback()
    if len(sys.argv) > 1:
        # Run Typer app without Click's default "Aborted!" message on Ctrl+C
        try:
            app(standalone_mode=False)
        except KeyboardInterrupt:
            pass
        except SystemExit:
            # Respect normal exits from Typer
            pass
    else:
        _windows_loop_patch()
        try:
            asyncio.run(run_loop())
        except KeyboardInterrupt:
            # Silent, fast exit on Ctrl+C
            pass
