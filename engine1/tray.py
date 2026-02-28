import os
import threading
import pystray
from pystray import Menu as TrayMenu, MenuItem as TrayItem
from PIL import Image

class TrayController:
    def __init__(self, tk_root, toggle_cmd, quit_cmd):
        self.tk_root = tk_root
        self.toggle_cmd = toggle_cmd
        self.quit_cmd = quit_cmd
        self.icon = None

    def _find_tray_icon(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for p in ["tray.png", "tray.ico", "icon.png", "icon.ico"]:
            full_path = os.path.join(base, "assets", p)
            if os.path.exists(full_path):
                return full_path
        return None

    def start(self):
        icon_path = self._find_tray_icon()
        if not icon_path:
            return

        try:
            image = Image.open(icon_path)
            menu = TrayMenu(
                TrayItem("Взаимодействие", self._toggle_safe, default=True),
                TrayItem("Выход", self._quit_safe),
            )
            self.icon = pystray.Icon("desktop-pet", image, "Desktop Pet", menu)
            threading.Thread(target=self.icon.run, daemon=True).start()
        except Exception:
            pass

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass

    def _toggle_safe(self, icon=None, item=None):
        try:
            self.tk_root.after(0, self.toggle_cmd)
        except Exception:
            pass

    def _quit_safe(self, icon=None, item=None):
        try:
            self.tk_root.after(0, self.quit_cmd)
        except Exception:
            pass
