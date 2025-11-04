import asyncio
import random
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, RichLog
from datetime import datetime

BOTS = [
    "Makima",
    "BoaHan",
    "RobNico",
    "Lucyna",
    "kjgy",
    "NeoBot",
    "LunaAI",
    "EchoX",
    "Yuki",
]
MESSAGES = [
    "That's wild!",
    "fr, can't believe it.",
    "u got a point.",
    "nahhh that's cap.",
    "bet, let's roll.",
    "bruh moment fr.",
    "no way!",
    "fr fr",
    "💀",
    "🔥🔥🔥",
    "LOL 😂",
]


class ChatLog(RichLog):
    """Simple scrollable text area for chat messages."""

    def __init__(self, highlight=False, markup=False):
        super().__init__(highlight=highlight, markup=markup)
        self.chat_log = []

    def add(self, msg: str):
        self.chat_log.append(msg)
        self.update_text()

    def update_text(self):
        line_w = 130
        for i in range(0, len(self.chat_log[-1]), line_w):
            self.write(self.chat_log[-1][i : i + line_w])


class ChatCLI(App):
    """chat TUI."""

    CSS = """
Screen {
    layout: vertical;
}
#chatlog {
    height: 1fr;
    border: round blue;
}
#status {
    border: none;
    content-align: right middle;
    color: gray;
}
#input-box {
    border: round black;
}
"""

    def __init__(self):
        super().__init__()
        self.voice = False
        self.mute = False
        self.start_time = datetime.now()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        self.status = Static(self._status_text(), markup=True)
        self.status.id = "status"
        yield self.status

        self.chat = ChatLog(highlight=True, markup=True)
        self.chat.id = "chatlog"
        yield self.chat

        self.input_box = Input(
            placeholder="type message | /v toggle mic | /m toggle mute | /q to exit"
        )
        self.input_box.id = "input-box"
        yield self.input_box

        yield Footer()

    def on_mount(self):
        self.set_interval(1, self._update_status)
        self.history = []
        self.history_index = 0
        self.action_focus_next()

    async def on_input_submitted(self, message: Input.Submitted):
        text = message.value.strip()
        self.input_box.value = ""

        if not text:
            return

        # store history
        self.history.append(text)
        self.history_index = len(self.history)

        if text in ("/v", "-v", "--voice"):
            self.voice = not self.voice
            self.chat.add(f"[green]* Voice {'ON' if self.voice else 'OFF'} *[/green]")
            return

        if text in ("/m", "-m", "--mute"):
            self.mute = not self.mute
            self.chat.add(f"[red]* Mute {'ON' if self.mute else 'OFF'} *[/red]")
            return

        if text in ("/q", "-q", "--quit"):
            await self.action_quit()
            return

        self.chat.add(f"[bold yellow]You:[/] {text}")

        if not self.mute:
            for bot in BOTS:
                await asyncio.sleep(random.uniform(0.3, 0.5))
                reply = random.choice(MESSAGES)
                self.chat.add(f"[bold blue]{bot}:[/] {reply}")

    async def on_key(self, event):
        if not self.input_box.has_focus:
            return
        if event.key == "up" and self.history:
            self.history_index = max(0, self.history_index - 1)
            self.input_box.value = self.history[self.history_index]
        elif event.key == "down" and self.history:
            self.history_index = min(len(self.history), self.history_index + 1)
            val = (
                self.history[self.history_index]
                if self.history_index < len(self.history)
                else ""
            )
            self.input_box.value = val

    def _status_text(self):
        mic = "🎙️" if self.voice else "🤫"
        sound = "🔇" if self.mute else "🔊"
        players = f"👤:{len(BOTS) + 1}"
        time_elapsed = datetime.now() - self.start_time
        seconds = time_elapsed.seconds
        minutes = seconds // 60
        hours = minutes // 60
        days = hours // 24
        if days > 0:
            time = f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            time = f"{hours}h {minutes}m {seconds}s"
        else:
            time = f"{minutes}m {seconds}s"
        return f"{mic} {sound} {players} | {time}"

    async def _update_status(self):
        self.status.update(self._status_text())
        self.status.refresh()


if __name__ == "__main__":
    ChatCLI().run()
