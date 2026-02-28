import random
import time


class Speech:
    def __init__(self):
        self._last_ms = 0
        self.cooldown_ms = 2500

    def _ok(self):
        now = int(time.monotonic() * 1000)
        if now - self._last_ms < self.cooldown_ms:
            return False
        self._last_ms = now
        return True

    def on_feed(self):
        if not self._ok():
            return None
        return random.choice([
            "О, спасибо!",
            "Ням.",
            "Ты лучший.",
        ])

    def on_play(self):
        if not self._ok():
            return None
        return random.choice([
            "Давай ещё!",
            "Ура!",
            "Мне весело.",
        ])

    def on_sleep(self):
        if not self._ok():
            return None
        return random.choice([
            "Спокойной ночи.",
            "Я подремлю.",
        ])

    def on_drag(self):
        if not self._ok():
            return None
        return random.choice([
            "Эй!",
            "Осторожнее...",
            "Куда мы?",
        ])
