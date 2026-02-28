import json
import os
from datetime import datetime

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pet_state.json")


class Pet:
    def __init__(self, name="Ганвест"):
        self.name = name
        self.hunger = 100
        self.energy = 100
        self.mood = 100
        self.state = "idle"
        self.bite_mode = False
        self.bite_count = 0
        self.is_sleeping = False
        self.good_weather = True

        # Накопители времени для tick(dt)
        self._hunger_acc = 0.0
        self._energy_acc = 0.0
        self._mood_acc = 0.0

        self.load_state()

    # ── Действия ──────────────────────────────────────────────

    def feed(self):
        self.hunger = min(100, self.hunger + 30)
        self.is_sleeping = False
        self.state = "eating"
        if self.bite_mode:
            self.bite_count += 1
        return f"🍖 {self.name} откусил кусок экрана!"

    def play(self):
        if self.energy < 10:
            return f"😴 {self.name} слишком устал"
        self.mood = min(100, self.mood + 25)
        self.energy = max(0, self.energy - 15)
        self.is_sleeping = False
        self.state = "playing"
        return f"🎾 {self.name} поиграл!"

    def sleep(self):
        self.is_sleeping = True
        self.state = "sleeping"
        return f"😴 {self.name} спит..."

    def wake(self):
        self.is_sleeping = False
        self.state = "idle"

    def reset_bites(self):
        self.bite_count = 0
        self.save_state()

    # ── Тик с dt ──────────────────────────────────────────────

    def tick(self, dt: float = 1.0):
        self._update_hunger(dt)
        self._update_energy(dt)
        self._update_mood(dt)
        if not self.is_sleeping:
            self.state = "idle"
        self.save_state()

    def _update_hunger(self, dt: float):
        # -1 каждые 10 секунд
        self._hunger_acc += dt
        ticks = int(self._hunger_acc / 10.0)
        if ticks:
            self._hunger_acc -= ticks * 10.0
            self.hunger = max(0, self.hunger - ticks)

    def _update_energy(self, dt: float):
        self._energy_acc += dt
        if self.is_sleeping:
            # +2 каждые 10 секунд во сне
            ticks = int(self._energy_acc / 10.0)
            if ticks:
                self._energy_acc -= ticks * 10.0
                self.energy = min(100, self.energy + ticks * 2)
                if self.energy >= 100:
                    self.is_sleeping = False
                    self.state = "idle"
        else:
            # -1 каждые 15 секунд
            ticks = int(self._energy_acc / 15.0)
            if ticks:
                self._energy_acc -= ticks * 15.0
                self.energy = max(0, self.energy - ticks)

    def _update_mood(self, dt: float):
        self._mood_acc += dt
        ticks = int(self._mood_acc / 8.0)
        if not ticks:
            return
        self._mood_acc -= ticks * 8.0

        delta = 0
        if self.good_weather:
            delta += 1
        else:
            delta -= 1

        if self.hunger < 20:
            delta -= 2
        elif self.hunger < 40:
            delta -= 1

        if self.energy < 20:
            delta -= 2
        elif self.energy < 40:
            delta -= 1

        if self.hunger > 70 and self.energy > 70:
            delta += 1

        self.mood = max(0, min(100, self.mood + delta * ticks))

    # ── Вспомогательные ───────────────────────────────────────

    def get_status(self):
        return f"{self.name}\n🍖 Голод: {self.hunger}\n⚡ Энергия: {self.energy}\n😊 Настроение: {self.mood}"

    def get_emotion(self):
        if self.mood > 70:
            return "👻"
        elif self.mood > 40:
            return "👻"
        else:
            return "💀"

    # ── Сохранение ────────────────────────────────────────────

    def save_state(self):
        try:
            data = {
                "name": self.name,
                "hunger": self.hunger,
                "energy": self.energy,
                "mood": self.mood,
                "bite_mode": self.bite_mode,
                "bite_count": self.bite_count,
                "is_sleeping": self.is_sleeping,
                "last_update": datetime.now().isoformat(),
            }
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def load_state(self):
        try:
            if not os.path.exists(SAVE_PATH):
                return
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.name = data.get("name", self.name)
            self.hunger = max(0, min(100, int(data.get("hunger", self.hunger))))
            self.energy = max(0, min(100, int(data.get("energy", self.energy))))
            self.mood = max(0, min(100, int(data.get("mood", self.mood))))
            self.bite_mode = bool(data.get("bite_mode", False))
            self.bite_count = int(data.get("bite_count", 0))
            self.is_sleeping = bool(data.get("is_sleeping", False))
        except Exception:
            pass
