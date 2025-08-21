# Friday

A personal AI for Tanav.
This repo now includes a simple, good-looking CLI powered by Pydantic AI and GUI with chainlit.

## Agentic Capabilities

- Knowledge base
- Speech recognition
- Whatsapp
- Search on the internet
- Open browser
- Save todos in `todos.csv`

## Project Structure

- `agent.py` — the agent that runs the AI
- `chainlit.py` — the chainlit UI
- `main.py` — the CLI
- `utils.py` — utilities working of the agent

## Setup

Clone the repo. (offcourse)

Install `uv (the most popular way of running python)` and run:

```bash
uv sync
```

> This runs the CLI with speech recognition.

```bash
uv run main.py
```

> This runs the GUI with Chainlit.

```bash
uv run chainlit run chainlit.py
```

## TODOs

Things I have to work on:

[-] Whatsapp mcp server
[ ] Eleven labs voice
[-] Chainlit UI
[-] Tech news
[-] private knowledge
[ ] streaming
