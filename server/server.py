import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
rooms = {}  

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_rooms():
    print("===== ROOM CREATION MENU =====")
    while True:
        room_id = input("Enter Room ID: ").strip()
        room_name = input("Enter Room Name: ").strip()
        max_users = int(input("Enter Max Users: ").strip())

        rooms[room_id] = {
            "name": room_name,
            "max": max_users,
            "clients": [],
            "voice_clients": []
        }
        print("✅ Room created")

        more = input("Add another room? (y/n): ").strip().lower()
        if more != "y":
            break

    print("\n✅ Server starting...")
    print("Available rooms:")
    for rid, info in rooms.items():
        print(f" - {rid} : {info['name']} (0/{info['max']} users)")


@app.get("/rooms")
def list_rooms():
    return {
        rid: {
            "name": info["name"],
            "max": info["max"],
            "users": len(info["clients"])
        }
        for rid, info in rooms.items()
    }


async def broadcast(room_id, message):
    for client in rooms[room_id]["clients"]:
        await client.send_text(message)


@app.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str):
    """Text chat endpoint"""
    if room_id not in rooms:
        await websocket.accept()
        await websocket.send_text("❌ Room does not exist!")
        await websocket.close()
        return

    if len(rooms[room_id]["clients"]) >= rooms[room_id]["max"]:
        await websocket.accept()
        await websocket.send_text("❌ Room full, cannot join!")
        await websocket.close()
        return

    await websocket.accept()
    rooms[room_id]["clients"].append(websocket)
    await broadcast(room_id, f"✅ {username} joined the room")

    try:
        while True:
            msg = await websocket.receive_text()
            await broadcast(room_id, f"{username}: {msg}")
    except WebSocketDisconnect:
        rooms[room_id]["clients"].remove(websocket)
        await broadcast(room_id, f"🚪 {username} left the room")


@app.websocket("/ws/voice/{room_id}/{username}")
async def voice_websocket(websocket: WebSocket, room_id: str, username: str):
    """Voice chat endpoint"""
    if room_id not in rooms:
        await websocket.accept()
        await websocket.send_bytes(b"ERR:NO_ROOM")
        await websocket.close()
        return

    if len(rooms[room_id]["voice_clients"]) >= rooms[room_id]["max"]:
        await websocket.accept()
        await websocket.send_bytes(b"ERR:ROOM_FULL")
        await websocket.close()
        return

    await websocket.accept()
    rooms[room_id]["voice_clients"].append(websocket)
    print(f"🎤 {username} joined voice in room {room_id}")

    try:
        while True:
            audio = await websocket.receive_bytes()
            for client in rooms[room_id]["voice_clients"]:
                if client != websocket:
                    await client.send_bytes(audio)
    except WebSocketDisconnect:
        rooms[room_id]["voice_clients"].remove(websocket)
        print(f"🔇 {username} left voice in room {room_id}")


if __name__ == "__main__":
    create_rooms()
    uvicorn.run(app, host="0.0.0.0", port=8000)
