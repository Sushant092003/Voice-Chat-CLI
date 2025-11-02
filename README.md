# ChatRoom (Python) - Text-first Prototype

This repository contains a minimal prototype of the ChatRoom project implemented in Python.
It includes a **FastAPI WebSocket server** and a **Typer-based CLI client** for interactive text chat.

## Features (MVP)
- Create/join rooms by room ID (server handles rooms in memory)
- Real-time text chat using WebSockets
- Simple CLI client to join and chat

## Structure
```
chatroom_python/
├── server/
│   └── server.py       # FastAPI WebSocket server
├── client/
│   └── client.py       # Typer CLI client (uses websockets)
├── requirements.txt
└── README.md
```

## Quick Start (local)

1. Create a virtual environment (recommended)
   ```sh
   python -m venv .venv
   source .venv/bin/activate   # Linux/Mac
   .\.venv\Scripts\activate  # Windows (PowerShell)
   ```

2. Install dependencies
   ```sh
   pip install -r requirements.txt
   ```

3. Run the server
   ```sh
   cd server
   python server.py
   # or: uvicorn server:app --reload --port 8000
   ```

4. Run the client (in another terminal)
   ```sh
   cd client
   python client.py join --room 1234 --name Alice
   ```

5. Open another client and join the same room:
   ```sh
   python client.py join --room 1234 --name Bob
   ```

Type messages in the client terminals and press Enter to send.

## Notes & Next Steps
- This is an in-memory, single-process server (rooms stored in Python dict). For production you should use persistent storage and user authentication.
- Voice support is not included in this initial prototype. For voice, consider using UDP streaming with `sounddevice` or `pyaudio`, and optionally a codec like Opus or aiortc for WebRTC.
- To expose the server publicly, deploy to a cloud/VPS and open the appropriate port (8000). For quick testing from remote machines, tools like `ngrok` can create a public tunnel.

## License
MIT
