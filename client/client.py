# client.py
import typer
import asyncio
import websockets
import sounddevice as sd
import numpy as np
import threading
import time
import keyboard  
import requests
from typing import Optional

app = typer.Typer()

# Server endpoints
SERVER_URL = "https://sneaking-sook-persnickety.ngrok-free.dev"
WS_CHAT = "wss://sneaking-sook-persnickety.ngrok-free.dev/ws"
WS_VOICE = "wss://sneaking-sook-persnickety.ngrok-free.dev/ws/voice"

# Audio config
SAMPLE_RATE = 16000
CHUNK = 1024
CHANNELS = 1
DTYPE = "int16"


mic_enabled = True
mute = False
push_to_talk = False
ptt_key = "space"  
voice_running = False
voice_restart_requested = False


mic_index: Optional[int] = None
speaker_index: Optional[int] = None


send_queue: Optional[asyncio.Queue] = None
play_queue: Optional[asyncio.Queue] = None


def find_realtek_device(kind="input"):
    try:
        devices = sd.query_devices()
    except Exception:
        return None
    for idx, dev in enumerate(devices):
        name = dev.get("name", "").lower()
        max_in = dev.get("max_input_channels", 0)
        max_out = dev.get("max_output_channels", 0)
        if "realtek" in name:
            if kind == "input" and max_in > 0:
                return idx
            if kind == "output" and max_out > 0:
                return idx
    return None


def audio_recorder_thread(loop, send_q: asyncio.Queue):
    global mic_index, mic_enabled, mute, push_to_talk, voice_running

    if mic_index is None:
        # Try default
        try:
            sd.check_input_settings(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE)
            mic_index_local = None
        except Exception:
            mic_index_local = None
    else:
        mic_index_local = mic_index

    
    try:
        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE,
                                blocksize=CHUNK, device=mic_index_local)
        stream.start()
        mic_enabled = True
    except Exception as e:
        mic_enabled = False
        print(f"⚠️ Mic unavailable -> Voice send disabled ({e})")
        return  

    voice_running = True
    try:
        while voice_running:
            try:
                data, overflowed = stream.read(CHUNK)
            except Exception as e:
                
                mic_enabled = False
                print(f"⚠️ Audio read error: {e}. Voice send disabled.")
                break

            
            if mute:
                continue

            if push_to_talk and not keyboard.is_pressed(ptt_key):
                continue

            # send bytes to asyncio queue (thread-safe)
            try:
                loop.call_soon_threadsafe(send_q.put_nowait, data.tobytes())
            except Exception:
                # If loop closed or queue full, ignore
                pass

    finally:
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass
        mic_enabled = False
        voice_running = False

# Audio playback thread
def audio_playback_thread(loop, play_q: asyncio.Queue, out_device_index):
    try:
        out_stream = sd.OutputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE,
                                     blocksize=CHUNK, device=out_device_index)
        out_stream.start()
    except Exception as e:
        print(f"⚠️ Output device error: {e}. Audio playback disabled.")
        return

    running = True
    while running:
        try:
            audio_bytes = asyncio.run_coroutine_threadsafe(play_q.get(), loop).result()
        except Exception:
            # loop closed or cancelled
            break
        if audio_bytes is None:
            break
        try:
            arr = np.frombuffer(audio_bytes, dtype=DTYPE)
            # ensure proper shape for stereo/mono
            try:
                out_stream.write(arr)
            except Exception as e:
                # write error — print and continue
                # print("Playback write error:", e)
                pass
        except Exception:
            pass

    try:
        out_stream.stop()
        out_stream.close()
    except Exception:
        pass

# Async coroutine: send queued audio bytes over websocket
async def voice_send_coroutine(ws):
    global send_queue
    if send_queue is None:
        return
    while True:
        try:
            data = await send_queue.get()
        except asyncio.CancelledError:
            break
        if data is None:
            break
        try:
            await ws.send(data)
        except Exception:
            break

# Async coroutine: receive audio bytes and enqueue for playback thread
async def voice_receive_coroutine(ws):
    global play_queue
    if play_queue is None:
        return
    while True:
        try:
            data = await ws.recv()
        except websockets.exceptions.ConnectionClosed:
            break
        except Exception:
            break
        # ensure binary
        if isinstance(data, (bytes, bytearray)):
            try:
                await play_queue.put(data)
            except Exception:
                pass

# Start voice subsystem: create queues, threads and connect to voice websocket
async def start_voice(room_id, username):
    global send_queue, play_queue, mic_index, speaker_index, voice_restart_requested, voice_running

    # detect devices
    mic_index = find_realtek_device("input")
    speaker_index = find_realtek_device("output")

    if mic_index is not None:
        print(f"🎤 Realtek mic detected (device index {mic_index})")
    else:
        print("⚠️ No Realtek mic found — voice send will be disabled unless default mic works")

    if speaker_index is not None:
        print(f"🔊 Realtek speaker detected (device index {speaker_index})")
    else:
        print("⚠️ No Realtek speaker found — using system default output")

    send_queue = asyncio.Queue()
    play_queue = asyncio.Queue()

    loop = asyncio.get_event_loop()

    # Start recorder thread (only if microphone available)
    recorder_thread = threading.Thread(target=audio_recorder_thread, args=(loop, send_queue), daemon=True)
    recorder_thread.start()

    # Start playback thread
    playback_thread = threading.Thread(target=audio_playback_thread, args=(loop, play_queue, speaker_index), daemon=True)
    playback_thread.start()

    # Connect websocket for voice
    url = f"{WS_VOICE}/{room_id}/{username}"
    try:
        async with websockets.connect(url) as ws:
            print("🎤 Voice websocket connected")
            # run send and receive coroutines concurrently
            send_task = asyncio.create_task(voice_send_coroutine(ws))
            recv_task = asyncio.create_task(voice_receive_coroutine(ws))
            done, pending = await asyncio.wait([send_task, recv_task], return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
    except Exception as e:
        print(f"⚠️ Voice websocket error: {e}")

    # cleanup
    try:
        # signal threads to exit by putting None
        if send_queue is not None:
            await send_queue.put(None)
        if play_queue is not None:
            await play_queue.put(None)
    except Exception:
        pass

    voice_running = False
    voice_restart_requested = False

# Text chat coroutines
async def chat_receive(ws):
    while True:
        try:
            msg = await ws.recv()
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Chat websocket closed")
            break
        except Exception as e:
            print("⚠️ Chat receive error:", e)
            break
        print(msg)

async def chat_send(ws, username):
    while True:
        # blocking input safely
        msg = await asyncio.get_event_loop().run_in_executor(None, input)
        if msg.strip() == "":
            continue
        # commands processed locally (do not send to server)
        if msg.startswith("/"):
            await handle_local_command(msg)
            continue
        try:
            await ws.send(msg)
        except Exception:
            break
        print(f"You: {msg}")

# Local command handler
async def handle_local_command(cmd: str):
    global mute, push_to_talk, voice_restart_requested
    cmd = cmd.strip()
    if cmd == "/mute":
        mute = True
        print("🔇 Muted (local)")
    elif cmd == "/unmute":
        mute = False
        print("🎙️ Unmuted (local)")
    elif cmd == "/ptt on":
        push_to_talk = True
        print(f"▶ Push-to-talk enabled (hold {ptt_key.upper()})")
    elif cmd == "/ptt off":
        push_to_talk = False
        print("▶ Push-to-talk disabled (open mic)")
    elif cmd == "/restart-voice":
        # request voice restart
        voice_restart_requested = True
        print("🔁 Voice restart requested")
    elif cmd == "/help":
        print("""Commands:
  /mute           - mute your mic locally
  /unmute         - unmute
  /ptt on         - enable push-to-talk (hold SPACE)
  /ptt off        - disable push-to-talk
  /restart-voice  - try to restart microphone streaming
  /help           - this help
""")
    else:
        print("Unknown command. Type /help")

# Combined join function: connects chat websocket and voice subsystem
async def run_client(room_id, username):
    # First check room exists via HTTP
    try:
        r = requests.get(f"{SERVER_URL}/rooms")
        rooms = r.json()
        if room_id not in rooms:
            print("❌ Room does not exist / not listed")
            return
    except Exception:
        print("⚠️ Could not fetch room list; proceeding to connect anyway")

    # start voice in background
    voice_task = asyncio.create_task(start_voice(room_id, username))

    # start chat connection
    chat_url = f"{WS_CHAT}/{room_id}/{username}"
    try:
        async with websockets.connect(chat_url) as ws:
            print(f"✅ Connected to chat in room {room_id} as {username}")
            # concurrently run send and receive
            send_task = asyncio.create_task(chat_send(ws, username))
            recv_task = asyncio.create_task(chat_receive(ws))

            # loop to watch for voice restart requests or task completion
            while True:
                done, pending = await asyncio.wait([send_task, recv_task, voice_task], return_when=asyncio.FIRST_COMPLETED, timeout=0.5)
                # if any chat task finished, break
                if send_task.done() or recv_task.done():
                    break
                # if voice restart requested by user, restart voice
                if voice_restart_requested:
                    # cancel existing voice_task and start new one
                    if not voice_task.done():
                        voice_task.cancel()
                        await asyncio.sleep(0.2)
                    voice_task = asyncio.create_task(start_voice(room_id, username))
                    # clear flag
                    # voice_restart_requested will be reset by start_voice end
                await asyncio.sleep(0.1)

            # cleanup
            for t in [send_task, recv_task]:
                if not t.done():
                    t.cancel()
    except Exception as e:
        print("⚠️ Chat connection error:", e)

# Typer CLI
@app.command()
def join(room_id: str, username: str):
    """Join room (chat + voice)"""
    asyncio.run(run_client(room_id, username))

if __name__ == "__main__":
    app()
