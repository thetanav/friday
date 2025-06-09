import time
import asyncio
import pyttsx3
from datetime import datetime
from dotenv import load_dotenv
import speech_recognition as sr
from pydantic_ai import Agent
from pydantic import BaseModel, Field

load_dotenv()


# Define a Pydantic model for structured AI responses
class FridayResponse(BaseModel):
    text: str = Field(description="The concise and helpful response from Friday.")


# Initialize the PydanticAI agent
agent = Agent(
    "google-gla:gemini-2.0-flash-lite",
    system_prompt="You are a personal AI for your master Tanav. Tanav made you with python and his sheer briliance. You owner is pro level coder as personal AI you always respond in short adn concise manner. Mainly for help. You can also tell the current time if asked.",
    output_type=FridayResponse,
)


@agent.tool
async def get_current_time() -> str:
    """Returns the current time."""
    return datetime.now().strftime("%H:%M:%S")


def tts(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.say(text)
    engine.runAndWait()


r = sr.Recognizer()


def test():
    tts("Hello how are you Tanav!")


async def main():
    with sr.Microphone() as source:
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio)
        print(">>> Tanav:", text)
        result = await agent.run(text)
        friday_response = result.output.text
        tts(friday_response)
        print(">>> Friday:", friday_response)
    except Exception as e:
        print(f"Error: {e}")
        pass
    time.sleep(0.5)


if __name__ == "__main__":
    # test()
    print(">>> Listening Active...")
    while True:
        asyncio.run(main())
