from datetime import datetime
import asyncio
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun
import webbrowser
from utils import _read_todos, _write_todos

load_dotenv()


class FridayResponse(BaseModel):
    text: str = Field(description="The concise and helpful response from Friday.")


search = DuckDuckGoSearchRun()

agent = Agent(
    "google-gla:gemini-2.0-flash-lite",
    system_prompt=(
        "You are a personal AI for your master Tanav. Tanav made you with python and his sheer briliance. "
        "You owner is pro level coder as personal AI you always respond in short and concise manner. "
        "Mainly for help. You can also tell the current time if asked. You behave as if your are Gilfolye from silicon valley."
        "My mummy is Rekha Gujar, he is exceptional teacher and lovely mummy, take with respect to him."
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
    print("    Searching ...")
    try:
        # DuckDuckGoSearchRun.run is synchronous; run it in a thread to avoid blocking the event loop
        result = await asyncio.to_thread(search.run, query)
        # Normalize result to a concise string
        if isinstance(result, list):
            text = "\n".join(str(r) for r in result[:5])
        else:
            text = str(result)
        # Keep output compact
        return text[:4000]
    except Exception as e:
        return f"Search failed: {e}"


@agent.tool_plain()
def open_browser_tab(query: str) -> None:
    """Open a new browser tab with the search results for the given query.
    Args:
        query (str): Only the keywords to open in new tab.
    """
    print("    Opening ...")
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
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
