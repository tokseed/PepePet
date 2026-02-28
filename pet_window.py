import os
import threading
import tkinter as tk
from tkinter import Menu
from enum import Enum, auto
import time
import requests
import queue
import pystray
from pystray import MenuItem as TrayItem, Menu as TrayMenu
from PIL import Image

from pet import Pet
from sprite_animator import SpriteAnimator

from win32api import GetMonitorInfo, MonitorFromPoint

try:
    from bite_overlay import BiteOverlay
except Exception:
    BiteOverlay = None

from engine2.windows_platforms import WindowsPlatforms


class ToolTip:
    def __init__(self, widget, text, delayms=350):
        self.widget = widget
        self.text = text
        self.delayms = delayms
        self.afterid = None
        self.tw = None
        widget.bind("<Enter>", self.onenter, add="+")
        widget.bind("<Leave>", self.onleave, add="+")
        widget.bind("<ButtonPress>", self.onleave, add="+")

    def onenter(self, event=None):
        self.cancel()
        self.afterid = self.widget.after(self.delayms, self.show)

    def onleave(self, event=None):
        self.cancel()
        self.hide()

    def cancel(self):
        if self.afterid:
            try:
                self.widget.after_cancel(self.afterid)
            except Exception:
                pass
        self.afterid = None

    def show(self):
        if self.tw:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tw = tk.Toplevel(self.widget)
        self.tw.overrideredirect(True)
        self.tw.attributes("-topmost", True)
        self.tw.configure(bg="#0f0f0f")
        self.tw.geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tw, text=self.text, bg="#0f0f0f", fg="white",
            relief="solid", borderwidth=1, font=("Segoe UI", 9),
        )
        label.pack(ipadx=6, ipady=3)

    def hide(self):
        if self.tw:
            try:
                self.tw.destroy()
            except Exception:
                pass
        self.tw = None


class ActionsPopup(tk.Toplevel):
    def __init__(self, masterwindow, callbacks):
        super().__init__(masterwindow)
        self.callbacks = callbacks
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="#000000")
        self.dragdx = 0
        self.dragdy = 0

        outer = tk.Frame(self, bg="#000000", padx=8, pady=8)
        outer.pack()

        dragbar = tk.Frame(outer, bg="#141414", height=10, cursor="fleur")
        dragbar.pack(fill="x", pady=(0, 8))
        dragbar.bind("<Button-1>", self.startdrag, add="+")
        dragbar.bind("<B1-Motion>", self.dodrag, add="+")

        btnframe = tk.Frame(outer, bg="#000000")
        btnframe.pack()

        def mkbtn(txt, cmd, tip):
            b = tk.Button(
                btnframe, text=txt, width=2, bd=1, relief="solid",
                highlightthickness=0, bg="#161616", fg="white",
                activebackground="#2b2b2b", activeforeground="white", command=cmd,
            )
            b.pack(side="left", padx=3)
            ToolTip(b, tip)
            return b

        mkbtn("🍖", self.callbacks["feed"], "Покормить")
        mkbtn("🎮", self.callbacks["play"], "Поиграть")
        mkbtn("💤", self.callbacks["sleep"], "Спать")
        mkbtn("🦷", self.callbacks["togglebite"], "Режим укусов (если есть модуль)")
        mkbtn("🧼", self.callbacks["resetbites"], "Сбросить укусы")
        mkbtn("✖", self.callbacks["quit"], "Выход")

    def startdrag(self, event):
        self.dragdx = event.x_root - self.winfo_x()
        self.dragdy = event.y_root - self.winfo_y()

    def dodrag(self, event):
        x = event.x_root - self.dragdx
        y = event.y_root - self.dragdy
        self.geometry(f"+{x}+{y}")


class MoveState(Enum):
    WALK = auto()
    FALL = auto()
    DRAG = auto()
    PAUSE = auto()


class HUDFollower(tk.Toplevel):
    def __init__(self, master, pet):
        super().__init__(master)
        self.pet = pet
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="white")
        self.attributes("-transparentcolor", "white")

        self.bar_width = 260
        self.bar_height = 18
        self.frame = tk.Frame(self, bg="white")
        self.frame.pack()

        # Имя питомца
        self.name_label = tk.Label(
            self.frame, text=getattr(pet, "name", ""),
            bg="white", fg="#111111",
            font=("Segoe UI", 10, "bold")
        )
        self.name_label.pack(pady=(0, 2))

        self.hunger = tk.Canvas(self.frame, width=self.bar_width, height=self.bar_height, bg="white", highlightthickness=0)
        self.hunger.pack(pady=3)
        self.energy = tk.Canvas(self.frame, width=self.bar_width, height=self.bar_height, bg="white", highlightthickness=0)
        self.energy.pack(pady=3)
        self.mood = tk.Canvas(self.frame, width=self.bar_width, height=self.bar_height, bg="white", highlightthickness=0)
        self.mood.pack(pady=3)
        self.update_bars()

    def _draw_badge_sticker(self, canvas, sticker):
        h = self.bar_height
        r = h // 2
        canvas.create_oval(14 - r, r - r, 14 + r, r + r, fill="#ffffff", outline="#ffffff")
        canvas.create_text(14, r, text=str(sticker), fill="#000000", font=("Segoe UI", 11, "bold"))

    def _draw_bar(self, canvas, value, color, bg_color, sticker):
        canvas.delete("all")
        w, h, r = self.bar_width, self.bar_height, self.bar_height // 2
        canvas.create_rectangle(r, 0, w - r, h, fill=bg_color, outline=bg_color)
        canvas.create_oval(0, 0, h, h, fill=bg_color, outline=bg_color)
        canvas.create_oval(w - h, 0, w, h, fill=bg_color, outline=bg_color)
        try:
            v = max(0, min(100, int(value)))
        except Exception:
            v = 0
        fill_w = max(0, min(w, int((v / 100) * w)))
        if fill_w > 0:
            if fill_w < h:
                canvas.create_oval(0, 0, h, h, fill=color, outline=color)
            else:
                canvas.create_rectangle(r, 0, fill_w - r, h, fill=color, outline=color)
                canvas.create_oval(0, 0, h, h, fill=color, outline=color)
                canvas.create_oval(fill_w - h, 0, fill_w, h, fill=color, outline=color)
        self._draw_badge_sticker(canvas, sticker)
        canvas.create_text(w - 16, h // 2, text=str(v), fill="white", font=("Segoe UI", 11, "bold"))

    def update_bars(self):
        self.name_label.configure(text=getattr(self.pet, "name", ""))
        self._draw_bar(self.hunger, getattr(self.pet, "hunger", 0), "#e74c3c", "#3d1a1a", "🍖")
        self._draw_bar(self.energy, getattr(self.pet, "energy", 0), "#3498db", "#1a2a3d", "⚡")
        self._draw_bar(self.mood, getattr(self.pet, "mood", 0), "#2ecc71", "#1a3d1a", "😊")



class OpenWeatherService:
    def __init__(self, lat, lon, api_key, on_update, interval_sec=600):
        self.lat = lat
        self.lon = lon
        self.api_key = api_key
        self.on_update = on_update
        self.interval_sec = interval_sec
        self._stop = False
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        if not self.api_key:
            return
        self.thread.start()

    def stop(self):
        self._stop = True

    def _run(self):
        while not self._stop:
            try:
                data = self._fetch_weather()
                if data is not None:
                    self.on_update(data)
            except Exception:
                pass
            time.sleep(self.interval_sec)

    def _fetch_weather(self):
        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?lat={self.lat}&lon={self.lon}&appid={self.api_key}&lang=ru&units=metric"
        )
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()


def is_good_weather(owm_json) -> bool:
    try:
        weather = owm_json.get("weather", [])
        if not weather:
            return True
        main = weather[0].get("main", "").lower()
        wid = int(weather[0].get("id", 800))
    except Exception:
        return True
    if main == "clear":
        return True
    if main == "clouds" and wid in (800, 801, 802):
        return True
    return False


PET_SIZE = 150
WINDOW_SIZE = 170


class PetWindow:
    def __init__(self, pet: Pet = None):
        self.pet = pet if pet is not None else Pet()
        self._last_tick = time.monotonic()


        self.root = tk.Tk()
        self.root.title("Desktop Pet")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="white")
        try:
            self.root.attributes("-transparentcolor", "white")
        except Exception:
            pass
        self.root.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE}+200+200")
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self.biteoverlay = None
        self.popup = None
        self.weather_q = queue.Queue()
        self.weather_json = None

        api_key = os.environ.get("OPENWEATHER_API_KEY", "").strip()
        self.weather = OpenWeatherService(
            lat=47.2313, lon=39.7233, api_key=api_key,
            on_update=lambda data: self.weather_q.put(data),
            interval_sec=600,
        )
        self.weather.start()
        self.root.after(250, self._weather_tick)

        self.offsetx = 0
        self.offsety = 0
        self.ismoving = False

        self.state = MoveState.WALK
        self.vx = 0.35
        self.vy = 0.0
        self.gravity = 0.35
        self.max_fall_speed = 10.0
        self.walk_dir = 1
        self.current_direction = self.walk_dir
        self.is_turning = False
        self.turn_duration = 800
        self.action_lock_ms = 0

        self.platform_refresh_ms = 250
        self.next_platform_refresh_ms = 0
        self.platforms_engine = WindowsPlatforms(self.get_work_area, self._exclude_hwnds)
        self.platforms_engine.refresh()

        self._outer_pad_y = 10
        self._outer_pad_x = 10

        self.petframe = tk.Frame(self.root, bg="white")
        self.petframe.pack(expand=True, fill="both", padx=self._outer_pad_x, pady=self._outer_pad_y)

        self.petcontainer = tk.Frame(self.petframe, bg="white", width=PET_SIZE, height=PET_SIZE)
        self.petcontainer.pack(expand=True)
        self.petcontainer.pack_propagate(False)

        self.petlabel = tk.Label(self.petcontainer, bg="white", borderwidth=0, highlightthickness=0)
        self.petlabel.place(relx=0.5, rely=0.5, anchor="center")

        self.menubutton = tk.Button(
            self.petcontainer, text="≡", font=("Segoe UI", 12, "bold"),
            bg="#0f0f0f", fg="white", bd=1, relief="solid", highlightthickness=0,
            activebackground="#2b2b2b", activeforeground="white",
            command=self.togglepopup, padx=5, pady=0,
        )
        self.menubutton.place(relx=1.0, rely=0.0, anchor="ne", x=-2, y=2)
        ToolTip(self.menubutton, "Меню")

        self.animator = SpriteAnimator(self.petlabel, fps=8, size=(PET_SIZE, PET_SIZE), fit=True)

        self._safe_loadanimation("walk_right")

        self.animator.preload([
            "walk_left", "turn_right", "turn_left", "idle",
            "eating", "playing", "sleeping", "happy", "sad", "fall"
        ])

        self.root.bind("<Button-1>", self.startdrag, add="+")
        self.root.bind("<B1-Motion>", self.drag, add="+")
        self.root.bind("<ButtonRelease-1>", self.stopdrag, add="+")
        self.root.bind("<Button-3>", self.showcontextmenu, add="+")

        self.contextmenu = Menu(self.root, tearoff=0)
        self.contextmenu.add_command(label="Покормить", command=self.feed)
        self.contextmenu.add_command(label="Поиграть", command=self.playaction)
        self.contextmenu.add_command(label="Спать", command=self.sleeppet)
        self.contextmenu.add_separator()
        self.contextmenu.add_checkbutton(label="Режим укусов", command=self.togglebitemode)
        self.contextmenu.add_command(label="Сбросить укусы", command=self.resetbites)
        self.contextmenu.add_separator()
        self.contextmenu.add_command(label="Выход", command=self.quit)

        self.tray_icon = None
        self._init_tray_safe()

        self.hud = HUDFollower(self.root, self.pet)
        self._hud_offset_y = 62
        self._hud_offset_x = 0
        self.follow_hud()

        if getattr(self.pet, "bite_mode", False) or getattr(self.pet, "bitemode", False):
            self.initbiteoverlay()

        self.root.after(1000, self._tick_loop)  # <-- заменено: было self.updatepet()
        self.animateloop()
        self.motion_loop()

    def _now_ms(self):
        return int(time.monotonic() * 1000)

    def get_work_area(self):
        monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
        return monitor_info.get("Work")

    def _exclude_hwnds(self):
        ids = []
        try:
            ids.append(self.root.winfo_id())
        except Exception:
            pass
        try:
            ids.append(self.hud.winfo_id())
        except Exception:
            pass
        try:
            if self.popup and self.popup.winfo_exists():
                ids.append(self.popup.winfo_id())
        except Exception:
            pass
        return ids

    def _safe_loadanimation(self, name: str) -> bool:
        try:
            return self.animator.load_anim(name)
        except Exception:
            return False

    def _set_anim(self, name: str):
        if self.animator.current_anim() == name:
            return
        if name in self.animator._loaded:
            self._safe_loadanimation(name)
        elif name == "idle":
            self._safe_loadanimation("idle")

    def _weather_tick(self):
        try:
            while True:
                data = self.weather_q.get_nowait()
                self.weather_json = data
        except Exception:
            pass
        if self.action_lock_ms == 0 and self.state != MoveState.DRAG and not self.is_turning:
            if self.weather_json is not None:
                good = is_good_weather(self.weather_json)
                self._set_anim("happy" if good else "sad")
        self.root.after(5000, self._weather_tick)

    def follow_hud(self):
        try:
            if not self.hud.winfo_exists():
                return
        except Exception:
            return
        self.root.update_idletasks()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        pet_w = self.root.winfo_width()
        hud_w = self.hud.bar_width
        hx = x + (pet_w // 2) - (hud_w // 2) + self._hud_offset_x
        hy = y - self._hud_offset_y
        self.hud.geometry(f"+{hx}+{hy}")
        self.hud.update_bars()
        self.root.after(33, self.follow_hud)

    def animateloop(self):
        try:
            interval = self.animator.animate()
            self.root.after(int(interval), self.animateloop)
        except Exception:
            self.root.after(80, self.animateloop)

    def motion_loop(self):
        self.step_motion()
        self.root.after(33, self.motion_loop)

    def _effective_body_height(self):
        try:
            self.root.update_idletasks()
            cont_h = self.petcontainer.winfo_height()
            return int(self._outer_pad_y + cont_h)
        except Exception:
            return int(self.root.winfo_height())

    def step_motion(self):
        if self.state == MoveState.DRAG:
            return

        now_ms = self._now_ms()
        if now_ms >= self.next_platform_refresh_ms:
            self.next_platform_refresh_ms = now_ms + self.platform_refresh_ms
            try:
                self.platforms_engine.refresh()
            except Exception:
                pass

        if self.action_lock_ms > 0:
            self.action_lock_ms = max(0, self.action_lock_ms - 33)
            return

        self.root.update_idletasks()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        w = self.root.winfo_width()
        h = self.root.winfo_height()

        wa_l, wa_t, wa_r, wa_b = self.get_work_area()
        body_h = self._effective_body_height()
        pet_left = x
        pet_right = x + w
        pet_body_bottom = y + body_h

        plat = None
        try:
            plat = self.platforms_engine.find_under(pet_left, pet_right, pet_body_bottom - 1, min_overlap=60)
        except Exception:
            plat = None

        if plat:
            plat_l, plat_y, plat_r = plat
            floor_y = plat_y - body_h
            min_x = max(plat_l, wa_l)
            max_x = min(plat_r - w, wa_r - w)
        else:
            floor_y = wa_b - body_h
            min_x = wa_l
            max_x = wa_r - w

        if min_x > max_x:
            min_x = wa_l
            max_x = wa_r - w

        floor_y = min(floor_y, wa_b - h)
        on_floor = (y >= floor_y - 2)

        if self.state == MoveState.FALL:
            self.vy = min(self.max_fall_speed, self.vy + self.gravity)
            y = y + int(self.vy)
            if y >= floor_y:
                y = floor_y
                self.vy = 0.0
                self.state = MoveState.WALK
                x = max(wa_l, min(x, wa_r - w))
                y = max(wa_t, min(y, wa_b - h))
                self.root.geometry(f"+{x}+{y}")
                return
            elif "fall" in self.animator._loaded:
                self._set_anim("fall")

        elif self.state == MoveState.WALK:
            if not on_floor:
                self.state = MoveState.FALL
                self.vy = 0.0
                return

            if not self.is_turning:
                x = x + int(self.walk_dir * self.vx * 10)
                hit_wall = False
                new_dir = self.walk_dir

                if x <= min_x:
                    x = min_x
                    hit_wall = True
                    new_dir = 1
                elif x >= max_x:
                    x = max_x
                    hit_wall = True
                    new_dir = -1

                if hit_wall and new_dir != self.walk_dir:
                    self.walk_dir = new_dir
                    self.start_turn(new_dir)
                else:
                    walk_anim = "walk_right" if self.walk_dir == 1 else "walk_left"
                    self._set_anim(walk_anim)

            y = floor_y
            self.vy = 0.0

        x = max(wa_l, min(x, wa_r - w))
        y = max(wa_t, min(y, wa_b - h))
        self.root.geometry(f"+{x}+{y}")

    def start_turn(self, new_dir: int):
        self.is_turning = True
        turn_anim = "turn_right" if new_dir == 1 else "turn_left"
        self.animator._current_anim = ""
        if self._safe_loadanimation(turn_anim):
            self.root.after(self.turn_duration, self.finish_turn, new_dir)
        else:
            self.finish_turn(new_dir)

    def finish_turn(self, new_dir: int):
        self.current_direction = new_dir
        self.is_turning = False
        self.animator._current_anim = ""
        walk_anim = "walk_right" if new_dir == 1 else "walk_left"
        if not self._safe_loadanimation(walk_anim):
            self._safe_loadanimation("idle")

    def startdrag(self, event):
        self.offsetx = event.x
        self.offsety = event.y
        self.ismoving = True
        self.state = MoveState.DRAG
        self.vy = 0.0

    def drag(self, event):
        if self.ismoving:
            x = self.root.winfo_x() + event.x - self.offsetx
            y = self.root.winfo_y() + event.y - self.offsety
            self.root.geometry(f"+{x}+{y}")

    def stopdrag(self, event):
        self.ismoving = False
        self.state = MoveState.WALK
        self.vy = 0.0

    def showcontextmenu(self, event):
        self.contextmenu.post(event.x_root, event.y_root)

    def feed(self):
        try:
            self.pet.feed()
        except Exception:
            pass
        self.action_lock_ms = 2000
        self.animator._current_anim = ""
        self._safe_loadanimation("eating")
        self.root.after(2000, self._finish_action)

    def playaction(self):
        if self.ismoving:
            return
        try:
            self.pet.play()
        except Exception:
            pass
        self.action_lock_ms = 2000
        self.animator._current_anim = ""
        self._safe_loadanimation("playing")
        self.root.after(2000, self._finish_action)

    def sleeppet(self):
        if self.ismoving:
            return
        try:
            self.pet.sleep()
        except Exception:
            pass
        self.action_lock_ms = 3000
        self.animator._current_anim = ""
        self._safe_loadanimation("sleeping")
        self.root.after(3000, self._finish_action)

    def _finish_action(self):
        self.animator._current_anim = ""
        self._safe_loadanimation("idle")

    def togglepopup(self):
        try:
            if self.popup and self.popup.winfo_exists():
                self.popup.destroy()
                self.popup = None
                return
        except Exception:
            self.popup = None

        callbacks = {
            "feed": self.feed, "play": self.playaction, "sleep": self.sleeppet,
            "togglebite": self.togglebitemode, "resetbites": self.resetbites, "quit": self.quit,
        }
        self.popup = ActionsPopup(self.root, callbacks)

        try:
            self.root.update_idletasks()
            self.popup.update_idletasks()
            rootx = self.root.winfo_rootx()
            rooty = self.root.winfo_rooty()
            rootw = self.root.winfo_width()
            popw = self.popup.winfo_width()
            poph = self.popup.winfo_height()
            x = rootx + rootw - popw - 2
            y = rooty - poph - 8
            if y < 0:
                y = rooty + 8
            self.popup.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _tray_quit(self, icon=None, item=None):
        try:
            self.root.after(0, self.quit)
        except Exception:
            pass

    def _tray_toggle_actions(self, icon=None, item=None):
        try:
            self.root.after(0, self.togglepopup)
        except Exception:
            pass

    def _find_tray_icon_path(self):
        base = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(base, "assets", "tray.ico"),
            os.path.join(base, "assets", "icon.ico"),
            os.path.join(base, "assets", "tray.png"),
            os.path.join(base, "assets", "icon.png"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    def _init_tray_safe(self):
        try:
            icon_path = self._find_tray_icon_path()
            if not icon_path:
                return
            image = Image.open(icon_path)
            menu = TrayMenu(
                TrayItem("Взаимодействие", self._tray_toggle_actions, default=True),
                TrayItem("Выход", self._tray_quit),
            )
            self.tray_icon = pystray.Icon("desktop-pet", image, "Desktop Pet", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception:
            self.tray_icon = None

    def togglebitemode(self):
        if hasattr(self.pet, "bite_mode"):
            self.pet.bite_mode = not self.pet.bite_mode
            if hasattr(self.pet, "save_state"):
                self.pet.save_state()
        elif hasattr(self.pet, "bitemode"):
            self.pet.bitemode = not self.pet.bitemode
            if hasattr(self.pet, "savestate"):
                self.pet.savestate()
        if getattr(self.pet, "bite_mode", False) or getattr(self.pet, "bitemode", False):
            self.initbiteoverlay()
        else:
            if self.biteoverlay:
                try:
                    self.biteoverlay.destroy()
                except Exception:
                    pass
                self.biteoverlay = None

    def initbiteoverlay(self):
        if BiteOverlay is None:
            return
        if self.biteoverlay is None:
            self.biteoverlay = BiteOverlay()

    def resetbites(self):
        if hasattr(self.pet, "reset_bites"):
            try:
                self.pet.reset_bites()
            except Exception:
                pass
        elif hasattr(self.pet, "resetbites"):
            try:
                self.pet.resetbites()
            except Exception:
                pass

    # <-- заменено: было updatepet()
    def _tick_loop(self):
        now = time.monotonic()
        dt = now - self._last_tick
        self._last_tick = now
        try:
            if self.weather_json is not None:
                self.pet.good_weather = is_good_weather(self.weather_json)
            self.pet.tick(dt)
        except Exception:
            pass
        try:
            self.hud.update_bars()
        except Exception:
            pass
        self.root.after(1000, self._tick_loop)

    def quit(self):
        try:
            self.weather.stop()
        except Exception:
            pass
        try:
            if hasattr(self.pet, "save_state"):
                self.pet.save_state()
            elif hasattr(self.pet, "savestate"):
                self.pet.savestate()
        except Exception:
            pass
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass
        try:
            if hasattr(self, "hud") and self.hud and self.hud.winfo_exists():
                self.hud.destroy()
        except Exception:
            pass
        try:
            if self.biteoverlay:
                self.biteoverlay.destroy()
        except Exception:
            pass
        try:
            if self.popup and self.popup.winfo_exists():
                self.popup.destroy()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    w = PetWindow()
    w.root.mainloop()
