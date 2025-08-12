import asyncio
from collections import deque
from typing import Deque, Tuple

import chainlit as cl

from agent import agent


# Simple memory per user session
HistoryType = Deque[Tuple[str, str]]


def build_contextual_prompt(history: HistoryType, user_msg: str) -> str:
    if history:
        convo = "\n".join(f"User: {u}\nFriday: {a}" for u, a in history)
    else:
        convo = "(no prior context)"
    if len(convo) > 4000:
        convo = convo[-4000:]
    return (
        "You are in an ongoing conversation.\n"
        "Conversation so far:\n"
        f"{convo}\n\n"
        f"Current user message: {user_msg}\n"
        "Respond as Friday, concise and helpful."
    )


@cl.on_chat_start
async def on_start():
    # Per-session short history
    cl.user_session.set("history", deque(maxlen=10))
    await cl.Message(content="Hi, I'm Friday. How can I help?").send()


@cl.on_message
async def on_message(msg: cl.Message):
    history: HistoryType = cl.user_session.get("history")  # type: ignore
    if history is None:
        history = deque(maxlen=10)
        cl.user_session.set("history", history)

    prompt = build_contextual_prompt(history, msg.content)

    # Placeholder message to update later
    res = await agent.run(prompt)
    text = res.output.text
    reply = cl.Message(content=text)
    await reply.send()

    # Update short history
    history.append((msg.content, text))
