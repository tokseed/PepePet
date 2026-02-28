from dataclasses import dataclass
from engine3.weather import WeatherState


@dataclass
class Reaction:
    anim: str | None = None     # имя gif-состояния (если есть)
    emoji: str | None = None    # fallback, если gif нет
    priority: int = 0
    ttl_ms: int = 4000


class WeatherReactor:
    """
    Правила:
    - temp < 1  -> дрожит
    - temp > 30 -> вентилятор
    - дождь     -> грустит
    Приоритет: вентилятор/дрожь выше грусти.
    """

    def reaction_for(self, w: WeatherState) -> Reaction | None:
        if w is None or w.temperature_c is None:
            return None

        # дождь
        if w.is_raining:
            r_rain = Reaction(anim="sad", emoji="☔", priority=10, ttl_ms=6000)
        else:
            r_rain = None

        # холод/жара
        if w.temperature_c < 1.0:
            return Reaction(anim="shiver", emoji="🥶", priority=30, ttl_ms=7000)
        if w.temperature_c > 30.0:
            return Reaction(anim="fan", emoji="🥵", priority=30, ttl_ms=7000)

        return r_rain
