import json
import os

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pet_state.json")


class Pet:
    def __init__(self):
        self.hunger = 80
        self.energy = 80
        self.mood = 80
        self.is_sleeping = False
        self.bite_mode = False

        # Накопители дробного времени (секунды)
        self._hunger_acc = 0.0
        self._energy_acc = 0.0
        self._mood_acc = 0.0

        # Внешние факторы
        self.good_weather = True

        self.load_state()

    # ── Действия ──────────────────────────────────────────────

    def feed(self):
        self.hunger = min(100, self.hunger + 30)
        self.is_sleeping = False

    def play(self):
        self.mood = min(100, self.mood + 20)
        self.energy = max(0, self.energy - 10)
        self.is_sleeping = False

    def sleep(self):
        self.is_sleeping = True

    def wake(self):
        self.is_sleeping = False

    def reset_bites(self):
        pass

    # ── Тик ───────────────────────────────────────────────────

    def tick(self, dt: float = 1.0):
        """
        dt — прошедшее время в секундах.
        Вызывать раз в секунду из PetWindow.
        """
        self._update_hunger(dt)
        self._update_energy(dt)
        self._update_mood(dt)
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
            # Спит — +2 каждые 10 секунд
            ticks = int(self._energy_acc / 10.0)
            if ticks:
                self._energy_acc -= ticks * 10.0
                self.energy = min(100, self.energy + ticks * 2)
                # Просыпается автоматически при полной энергии
                if self.energy >= 100:
                    self.is_sleeping = False
        else:
            # Бодрствует — -1 каждые 15 секунд
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

        # Погода
        if self.good_weather:
            delta += 1
        else:
            delta -= 1

        # Голод и энергия тянут настроение вниз
        if self.hunger < 20:
            delta -= 2
        elif self.hunger < 40:
            delta -= 1

        if self.energy < 20:
            delta -= 2
        elif self.energy < 40:
            delta -= 1

        # Сытость и бодрость поднимают настроение
        if self.hunger > 70 and self.energy > 70:
            delta += 1

        self.mood = max(0, min(100, self.mood + delta * ticks))

    # ── Сохранение ────────────────────────────────────────────

    def save_state(self):
        try:
            data = {
                "hunger": self.hunger,
                "energy": self.energy,
                "mood": self.mood,
                "is_sleeping": self.is_sleeping,
                "bite_mode": self.bite_mode,
            }
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def load_state(self):
        try:
            if not os.path.exists(SAVE_PATH):
                return
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.hunger = max(0, min(100, int(data.get("hunger", self.hunger))))
            self.energy = max(0, min(100, int(data.get("energy", self.energy))))
            self.mood = max(0, min(100, int(data.get("mood", self.mood))))
            self.is_sleeping = bool(data.get("is_sleeping", False))
            self.bite_mode = bool(data.get("bite_mode", False))
        except Exception:
            pass
