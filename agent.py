import asyncio
import webbrowser
from ddgs import DDGS
from datetime import datetime
from pydantic_ai import Agent
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from utils import _read_todos, _write_todos

try:
    import pywhatkit as pwk
except Exception:
    pwk = None

load_dotenv()


class FridayResponse(BaseModel):
    text: str = Field(description="The concise and helpful response from Friday.")


agent = Agent(
    "google-gla:gemini-2.5-flash-lite",
    system_prompt=(
        "You are a personal AI for your master Tanav. Tanav made you with python and his sheer briliance. "
        "You owner is pro level coder as personal AI you always respond in short and concise manner. "
        "Mainly for help. You can also tell the current time if asked. You behave as if your are Gilfolye from silicon valley."
        "My mummy is Rekha Gujar, he is exceptional teacher and lovely mummy, take with respect to him."
        "When you use tools, integrate the tool results directly into your final answer with 1-3 concise bullets."
    ),
    output_type=FridayResponse,
)


@agent.tool_plain()
def get_current_time() -> str:
    """Returns the current date and time."""
    return datetime.now().strftime("%B %d, %Y at %I:%M %p")


@agent.tool_plain()
async def search_web(query: str) -> str:
    """Search the web for a query.
    Args:
        query (str): The query to search on internet.
    """
    # Minimal hint that a tool was invoked; the CLI shows a spinner.
    print(" ✦ Searching Web ...")
    try:

        def _search(q: str):
            with DDGS() as ddgs:
                return list(
                    ddgs.text(q, region="in-en", safesearch="moderate", max_results=5)
                )

        results = await asyncio.to_thread(_search, query)
        if not results:
            return f"No results found for: {query}"
        lines: list[str] = []
        for i, r in enumerate(results[:5], 1):
            title = (r.get("title") or "Untitled").strip()
            href = (r.get("href") or "").strip()
            body = (r.get("body") or "").strip()
            snippet = body[:160] + ("…" if len(body) > 160 else "")
            lines.append(f"{i}. {title}\n   {href}\n   {snippet}")
        return "\n".join(lines)[:4000]
    except Exception as e:
        return f"Search failed: {e}"


@agent.tool_plain()
def open_browser_tab(url: str) -> None:
    """Open a Url in a new browser tab.
    Args:
        url (str): URL to open in the new tab.
    """
    print(" ✦ Opening Browser ...")
    webbrowser.open_new_tab(url)


# tools for adding
@agent.tool_plain()
def add_todo_item(item: str) -> str:
    """Add a new todo item.
    Args:
        item (str): The todo item to add.
    """
    text = (item or "").strip()
    if not text:
        return "Ignored empty todo item."
    todos = _read_todos()
    # Avoid exact duplicates (case-insensitive)
    if any(t.lower() == text.lower() for t in todos):
        return f"Todo already exists: {text}"
    todos.append(text)
    _write_todos(todos)
    return f"Added todo: {text}"


# removing todo
@agent.tool_plain()
def remove_todo_item(item: str) -> str:
    """Remove a todo item.
    Args:
        item (str): The todo item to remove.
    """
    text = (item or "").strip()
    if not text:
        return "Provide a todo to remove."
    todos = _read_todos()
    before = len(todos)
    filtered = [t for t in todos if t.lower() != text.lower()]
    if len(filtered) == before:
        return f"Todo not found: {text}"
    _write_todos(filtered)
    removed = before - len(filtered)
    return f"Removed {removed} item(s): {text}"


# showing todos from a csv file
@agent.tool_plain()
def show_todo_items() -> list[str]:
    """Show all todo items.
    Returns:
        list[str]: A list of all todo items.
    """
    return _read_todos()


@agent.tool_plain()
def whatsapp_send_now(phone_e164: str, message: str) -> str:
    """Send a WhatsApp message immediately via web.whatsapp.com
        to send message to the person use number given below.

    Papa number: "+919983337125"
    Mummy number: "+919261188538"

    Args:
        phone_e164: Recipient phone number.
        message: The message text to send.

    Notes:
        - This opens web.whatsapp.com in the default browser and attempts to send.
        - Ensure you're logged in to WhatsApp Web.
    """
    print(" ✦ Using Whatsapp ...")
    phone = (phone_e164 or "").strip()
    if not phone.startswith("+") or len(phone) < 8:
        return "Provide phone in E.164 format, e.g., +919876543210"
    if not (message or "").strip():
        return "Message cannot be empty"
    if pwk is None:
        return "pywhatkit is not available; install dependencies and try again"
    try:
        pwk.sendwhatmsg_instantly(phone_no=phone, message=message, tab_close=True)
        return f"Sent WhatsApp message to {phone}"
    except Exception as e:
        return f"Failed to send WhatsApp message: {e}"
