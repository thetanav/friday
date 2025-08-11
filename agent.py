from datetime import datetime
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class FridayResponse(BaseModel):
    text: str = Field(description="The concise and helpful response from Friday.")


agent = Agent(
    "google-gla:gemini-2.0-flash-lite",
    system_prompt=(
        "You are a personal AI for your master Tanav. Tanav made you with python and his sheer briliance. "
        "You owner is pro level coder as personal AI you always respond in short and concise manner. "
        "Mainly for help. You can also tell the current time if asked. You behave as if your are Gilfolye from silicon valley."
    ),
    output_type=FridayResponse,
)


@agent.tool
async def get_current_time(_ctx=None) -> str:
    """Returns the current data and time."""
    return datetime.now().strftime("%B %d, %Y at %I:%M %p")
