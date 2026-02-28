import ctypes
import ctypes.wintypes

import win32gui
import win32con


class WindowsPlatforms:
    """
    Платформы = верхние грани видимых окон + "земля" (низ WorkArea).

    Фильтры:
    - окно видимое, имеет заголовок;
    - НЕ minimized (по GetWindowPlacement.showCmd и IsIconic); [web:374][web:366]
    - пересекается с WorkArea (на экране);
    - не toolwindow, не слишком маленькое.

    Границы окна: DWM extended frame bounds (точнее, меньше "висит"). [web:324][web:354]
    """

    DWMWA_EXTENDED_FRAME_BOUNDS = 9  # [web:324]

    def __init__(self, get_work_area_callable, exclude_hwnds_callable=None):
        self.get_work_area = get_work_area_callable
        self.exclude_hwnds_callable = exclude_hwnds_callable
        self.platforms = []

        try:
            self._dwm_get_window_attribute = ctypes.windll.dwmapi.DwmGetWindowAttribute
        except Exception:
            self._dwm_get_window_attribute = None

    def _exclude_hwnds(self):
        if self.exclude_hwnds_callable:
            try:
                return set(self.exclude_hwnds_callable())
            except Exception:
                return set()
        return set()

    def _get_rect_dwm(self, hwnd):
        if not self._dwm_get_window_attribute:
            return None
        rect = ctypes.wintypes.RECT()
        res = self._dwm_get_window_attribute(
            ctypes.wintypes.HWND(hwnd),
            ctypes.wintypes.DWORD(self.DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(rect),
            ctypes.sizeof(rect),
        )
        if res != 0:
            return None
        return (int(rect.left), int(rect.top), int(rect.right), int(rect.bottom))

    def _get_rect(self, hwnd):
        r = self._get_rect_dwm(hwnd)
        if r is not None:
            return r
        return win32gui.GetWindowRect(hwnd)

    def _is_minimized(self, hwnd):
        # 1) Быстрый тест minimized [web:366]
        try:
            if win32gui.IsIconic(hwnd):
                return True
        except Exception:
            pass

        # 2) Надёжный тест через placement showCmd = SW_SHOWMINIMIZED [web:374]
        try:
            placement = win32gui.GetWindowPlacement(hwnd)  # tuple: (flags, showCmd, minpos, maxpos, normalpos) [web:372]
            show_cmd = placement[1]
            return show_cmd == win32con.SW_SHOWMINIMIZED
        except Exception:
            return False

    def _is_good_window(self, hwnd, exclude_hwnds, min_w=180, min_h=80):
        try:
            if not win32gui.IsWindow(hwnd):
                return False
            if hwnd in exclude_hwnds:
                return False
            if not win32gui.IsWindowVisible(hwnd):
                return False
            if self._is_minimized(hwnd):
                return False

            title = win32gui.GetWindowText(hwnd)
            if not title:
                return False

            exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if exstyle & win32con.WS_EX_TOOLWINDOW:
                return False

            l, t, r, b = self._get_rect(hwnd)
            if (r - l) < min_w or (b - t) < min_h:
                return False

            # только то, что реально на экране (пересекает work area) [web:322]
            wa_l, wa_t, wa_r, wa_b = self.get_work_area()
            if r <= wa_l or l >= wa_r or b <= wa_t or t >= wa_b:
                return False

            return True
        except Exception:
            return False

    def refresh(self):
        platforms = []

        wa_l, wa_t, wa_r, wa_b = self.get_work_area()
        platforms.append((wa_l, wa_b, wa_r, wa_b + 1))  # земля

        exclude_hwnds = self._exclude_hwnds()

        def enum_cb(hwnd, _):
            if self._is_good_window(hwnd, exclude_hwnds):
                try:
                    l, t, r, b = self._get_rect(hwnd)
                    platforms.append((l, t, r, t + 1))
                except Exception:
                    pass
            return True

        win32gui.EnumWindows(enum_cb, None)  # [web:351]
        self.platforms = platforms
        return platforms

    def find_under(self, pet_left, pet_right, pet_bottom, max_drop=2000, min_overlap=60):
        best_y = None
        best = None

        for l, y, r, _ in self.platforms:
            overlap = min(pet_right, r) - max(pet_left, l)
            if overlap < min_overlap:
                continue

            if y < pet_bottom:
                continue

            dy = y - pet_bottom
            if dy > max_drop:
                continue

            if best_y is None or y < best_y:
                best_y = y
                best = (l, y, r)

        return best
