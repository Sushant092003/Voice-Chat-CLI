# ChatRoom (Python)

Minimal CLI chat system built with **FastAPI** and **WebSockets**.
Includes a **server** and **CLI client** for real-time room-based chat.

## Features

- Create/join chat rooms by room ID
- Real-time text chat via WebSockets
- Typer-based CLI client
- In-memory room management (no DB yet)

## Structure

```
chatroom_python/
├── server/
│   └── server.py       # FastAPI WebSocket server
├── client/
│   └── client.py       # Typer CLI client
├── requirements.txt
└── README.md
```

## Quick Start (local)

_This project uses the `uv` package manager._

1. **Install dependencies**

   ```sh
   uv sync
   ```

2. **Run the server**

   ```sh
   cd server
   uv run server.py
   # or:
   uv run uvicorn server:app --reload --port 8000
   ```

3. **Run a client**

   ```sh
   cd client
   uv run client.py 1234 Alice
   ```

4. **Open another client (same room)**

   ```sh
   uv run client.py 1234 Bob
   ```

Then just type messages and hit Enter to chat.

## Notes & Next Steps

- Rooms are stored in memory — no persistence or auth yet.
- Add persistence (Redis, DB) for multi-instance setups.
- Voice support planned (likely via UDP or WebRTC).
- For remote testing, use tools like `ngrok` to expose port `8000`.

## References

- [Weechat](https://weechat.org/)
- [Simplex Chat](https://simplex.chat/docs/cli.html)

## License

MIT
