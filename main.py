import asyncio
import sys
from collections import deque
from utils import tts
import speech_recognition as sr
from agent import agent
from agent import whatsapp_send_now as _wa_send_now
from rich.console import Console
from rich.panel import Panel
from rich import box
import typer
from rich.prompt import Prompt


running = True  # Global flag to control the main loop (kept for compatibility)
console = Console()
app = typer.Typer(help="Friday CLI – voice and text modes")


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
            console.print("[yellow]Didn’t catch that. Try again…[/]")
            return None
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
                user_text = await recognize_speech_once()
            except EOFError:
                break

            if not user_text:
                await asyncio.sleep(0.1)
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
            # Show a spinner while Friday is thinking
            # Minimal tool breadcrumbs: the tools print lines starting with [tool]
            with console.status("Thinking…", spinner="dots"):
                result = await agent.run(contextual_prompt)
            friday_response = result.output.text
            console.print(
                Panel.fit(
                    friday_response,
                    title="Friday",
                    border_style="cyan",
                    box=box.ROUNDED,
                )
            )
            await tts(friday_response)

            # Update history
            history.append((user_text, friday_response))

            await asyncio.sleep(0.1)
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


# ----- CLI commands -----


def _windows_loop_patch():
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass


@app.command(help="Start voice listening mode")
def listen():
    _windows_loop_patch()
    asyncio.run(run_loop())


@app.command(help="Ask Friday a one-off question")
def ask(
    question: str = typer.Argument(..., help="Your question"),
    speak: bool = typer.Option(False, "--speak", help="Read the reply aloud"),
):
    _windows_loop_patch()

    async def _run():
        try:
            with console.status("Thinking…", spinner="dots"):
                res = await agent.run(question)
            reply = res.output.text
            console.print(
                Panel.fit(reply, title="Friday", border_style="cyan", box=box.ROUNDED)
            )
            if speak:
                await tts(reply)
        except KeyboardInterrupt:
            console.print("[dim]Cancelled.[/]")

    asyncio.run(_run())


@app.command(help="Interactive text chat session")
def chat(speak: bool = typer.Option(False, "--speak", help="Read replies aloud")):
    _windows_loop_patch()

    console.print(
        Panel(
            "Type messages to chat with Friday. Press q to quit. Ctrl+C cancels a reply.",
            title="Friday Chat",
            border_style="magenta",
            box=box.ROUNDED,
        )
    )
    history: deque[tuple[str, str]] = deque(maxlen=10)

    async def _loop():
        while True:
            try:
                user = Prompt.ask("You")
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Bye.[/]")
                break

            if not user.strip():
                continue
            if user.strip().lower() in {"q", ":q", "/q", "quit", "exit"}:
                console.print("[dim]Bye.[/]")
                break

            if history:
                convo = "\n".join(f"User: {u}\nFriday: {a}" for u, a in history)
            else:
                convo = "(no prior context)"
            if len(convo) > 4000:
                convo = convo[-4000:]

            contextual_prompt = (
                "You are in an ongoing conversation.\n"
                "Conversation so far:\n"
                f"{convo}\n\n"
                f"Current user message: {user}\n"
                "Respond as Friday, concise and helpful."
            )

            try:
                with console.status("Thinking…", spinner="dots"):
                    res = await agent.run(contextual_prompt)
                reply = res.output.text
                console.print(
                    Panel.fit(
                        reply, title="Friday", border_style="cyan", box=box.ROUNDED
                    )
                )
                if speak:
                    await tts(reply)
                history.append((user, reply))
            except KeyboardInterrupt:
                console.print("[dim]Cancelled.[/]")

    asyncio.run(_loop())


if __name__ == "__main__":
    # Backward-compatible default: no args -> listen, else CLI
    if len(sys.argv) > 1:
        app()
    else:
        _windows_loop_patch()
        asyncio.run(run_loop())


# ---- WhatsApp CLI ----

whatsapp = typer.Typer(help="WhatsApp tools using pywhatkit")


@whatsapp.command(
    "send-now", help="Send a WhatsApp message immediately via WhatsApp Web"
)
def wa_send_now(
    phone: str = typer.Argument(..., help="Phone in E.164, e.g., +919876543210"),
    message: str = typer.Argument(..., help="Message text"),
):
    res = _wa_send_now(phone, message)
    console.print(
        Panel.fit(res, title="WhatsApp", border_style="green", box=box.ROUNDED)
    )


app.add_typer(whatsapp, name="whatsapp")
