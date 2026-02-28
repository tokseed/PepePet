import json
import threading
import time
import urllib.request
from dataclasses import dataclass


@dataclass
class WeatherState:
    temperature_c: float | None = None
    precipitation_mm: float | None = None
    is_raining: bool = False
    updated_at: float | None = None
    error: str | None = None


class WeatherService:
    """
    Open-Meteo: без API ключа. Берём текущую температуру и precipitation. [web:381]
    Работает в фоне: poll() блокирует сеть, поэтому запускаем в отдельном thread и публикуем результат в callback.
    """

    def __init__(self, lat: float, lon: float, on_update, interval_sec: int = 600, timeout_sec: int = 8):
        self.lat = lat
        self.lon = lon
        self.on_update = on_update
        self.interval_sec = interval_sec
        self.timeout_sec = timeout_sec

        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            st = self.fetch_once()
            try:
                self.on_update(st)
            except Exception:
                pass
            for _ in range(self.interval_sec):
                if self._stop.is_set():
                    break
                time.sleep(1)

    def fetch_once(self) -> WeatherState:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={self.lat}&longitude={self.lon}"
            "&current=temperature_2m,precipitation"
        )
        try:
            with urllib.request.urlopen(url, timeout=self.timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            cur = data.get("current") or {}
            temp = cur.get("temperature_2m")
            precip = cur.get("precipitation")

            is_rain = False
            try:
                # precipitation в мм; >0 значит есть осадки (для твоего “идёт дождь → грустит” достаточно)
                is_rain = float(precip) > 0.0
            except Exception:
                is_rain = False

            return WeatherState(
                temperature_c=float(temp) if temp is not None else None,
                precipitation_mm=float(precip) if precip is not None else None,
                is_raining=is_rain,
                updated_at=time.time(),
                error=None,
            )
        except Exception as e:
            return WeatherState(error=str(e), updated_at=time.time())
