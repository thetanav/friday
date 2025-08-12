# Friday — Chainlit UI

A concise personal AI for Tanav, powered by Gemini 2.5 Flash Lite and running with Chainlit.

## What you can do

- Quick answers and help in short, crisp replies.
- Tools:
  - Time: “what's the time?”
  - Web search (DuckDuckGo): “search web for…”.
  - Open a link: “open https://example.com”.
  - Todos (stored in `todos.csv`)
  - WhatsApp (WhatsApp Web via pywhatkit)

## Using this UI

- Type your message below; Friday replies concisely.
- Short-term memory: last 10 exchanges are used for context.
- Links you ask to open will launch in a new browser tab.

## Run locally

- Start the app:

```bash
uv run chainlit run chainlit.py --watch
```

Notes: ensure required API keys/dependencies are configured in your environment; WhatsApp actions need you signed in to web.whatsapp.com.
