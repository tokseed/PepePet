import os
import json
import tkinter as tk
from PIL import Image, ImageTk
from pet import Pet
from pet_window import PetWindow

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pet_state.json")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

print("[DEBUG] SAVE_PATH:", SAVE_PATH)
print("[DEBUG] pet_state.json exists:", os.path.exists(SAVE_PATH))
if os.path.exists(SAVE_PATH):
    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        print("[DEBUG] pet_state.json content:", f.read())


def _has_save() -> bool:
    try:
        if not os.path.exists(SAVE_PATH):
            return False
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return bool(data.get("name", "").strip())
    except Exception:
        return False


def save_pet(pet: Pet):
    data = {
        "name": getattr(pet, "name", "Питомец"),
        "hunger": getattr(pet, "hunger", 100),
        "energy": getattr(pet, "energy", 100),
        "mood": getattr(pet, "mood", 100),
        "bite_mode": getattr(pet, "bite_mode", False),
        "bite_count": getattr(pet, "bite_count", 0),
        "is_sleeping": getattr(pet, "is_sleeping", False),
    }
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


def load_pet() -> Pet:
    if not os.path.exists(SAVE_PATH):
        return Pet()
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return Pet()

    name = data.get("name") or "Питомец"
    pet = Pet(name=name)
    for attr in ("hunger", "energy", "mood", "bite_mode", "bite_count", "is_sleeping"):
        if hasattr(pet, attr) and attr in data:
            try:
                setattr(pet, attr, data[attr])
            except Exception:
                pass
    return pet


def _make_bg(root, w, h):
    canvas = tk.Canvas(root, width=w, height=h, highlightthickness=0, borderwidth=0)
    canvas.place(x=0, y=0)

    for fname in os.listdir(ASSETS_DIR):
        if fname.lower() == "background_menu.jfif":
            bg_path = os.path.join(ASSETS_DIR, fname)
            try:
                bg_img = Image.open(bg_path).resize((w, h), Image.LANCZOS)
                bg_photo = ImageTk.PhotoImage(bg_img)
                canvas.bg_photo = bg_photo
                canvas.create_image(0, 0, anchor="nw", image=bg_photo)
            except Exception:
                canvas.configure(bg="#0f0f0f")
            break
    else:
        canvas.configure(bg="#0f0f0f")

    return canvas


TITLE_FONT = ("Yu Gothic UI", 16, "bold")
SUBTITLE_FONT = ("Yu Gothic UI", 11, "bold")

TEXT_MAIN = "#FF0000"
TEXT_SUB = "#FF0000"


def show_welcome() -> str:
    root = tk.Tk()
    root.title("Новый питомец")
    root.resizable(False, False)
    w, h = 340, 220
    sx = (root.winfo_screenwidth() - w) // 2
    sy = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{sx}+{sy}")

    canvas = _make_bg(root, w, h)

    canvas.create_text(
        w // 2, 40,
        text="🐾 Виртуальный питомец",
        fill=TEXT_MAIN,
        font=TITLE_FONT,
    )
    canvas.create_text(
        w // 2, 72,
        text="Как назовёшь питомца?",
        fill=TEXT_SUB,
        font=SUBTITLE_FONT,
    )

    name_var = tk.StringVar()
    entry = tk.Entry(
        root, textvariable=name_var,
        font=("Yu Gothic UI", 12),
        bg="#1e1e1e", fg="white",
        insertbackground="white",
        relief="flat", justify="center",
    )
    canvas.create_window(w // 2, 115, window=entry, width=220, height=32)
    entry.focus()

    result = {"name": "Питомец"}

    def on_create():
        result["name"] = name_var.get().strip() or "Питомец"
        root.destroy()

    btn = tk.Button(
        root, text="Создать",
        font=("Yu Gothic UI", 11, "bold"),
        bg="#000000", fg="#FF0000",
        activebackground="#000000", activeforeground="#FF4444",
        relief="flat", cursor="hand2",
        command=on_create, padx=24, pady=6,
    )
    canvas.create_window(w // 2, 170, window=btn)

    root.bind("<Return>", lambda e: on_create())
    root.mainloop()
    return result["name"]


def show_main_menu() -> str:
    choice = {"value": "continue"}

    root = tk.Tk()
    root.title("Desktop Pet")
    root.resizable(False, False)
    w, h = 360, 220
    sx = (root.winfo_screenwidth() - w) // 2
    sy = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{sx}+{sy}")

    canvas = _make_bg(root, w, h)

    pet_name = "питомец"
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            pet_name = json.load(f).get("name", "питомец")
    except Exception:
        pass

    canvas.create_text(
        w // 2, 40,
        text="🐾 Виртуальный питомец",
        fill=TEXT_MAIN,
        font=TITLE_FONT,
    )
    canvas.create_text(
        w // 2, 72,
        text=f"Твой питомец: {pet_name}",
        fill=TEXT_SUB,
        font=SUBTITLE_FONT,
    )

    def on_continue():
        choice["value"] = "continue"
        root.destroy()

    def on_new():
        choice["value"] = "new"
        root.destroy()

    btn_continue = tk.Button(
        root, text="▶  Продолжить",
        font=("Yu Gothic UI", 11, "bold"),
        bg="#000000", fg="#FF0000",
        activebackground="#000000", activeforeground="#FF4444",
        relief="flat", cursor="hand2",
        command=on_continue, padx=20, pady=6,
    )
    canvas.create_window(w // 2 - 80, 150, window=btn_continue)

    btn_new = tk.Button(
        root, text="✦  Новая игра",
        font=("Yu Gothic UI", 11, "bold"),
        bg="#000000", fg="#FF0000",
        activebackground="#000000", activeforeground="#FF4444",
        relief="flat", cursor="hand2",
        command=on_new, padx=20, pady=6,
    )
    canvas.create_window(w // 2 + 80, 150, window=btn_new)

    root.bind("<Return>", lambda e: on_continue())
    root.mainloop()
    return choice["value"]


if __name__ == "__main__":
    if _has_save():
        action = show_main_menu()
        if action == "new":
            if os.path.exists(SAVE_PATH):
                try:
                    os.remove(SAVE_PATH)
                except Exception:
                    pass
            name = show_welcome()
            pet = Pet(name=name)
        else:
            pet = load_pet()
    else:
        name = show_welcome()
        pet = Pet(name=name)

    w = PetWindow(pet)
    try:
        w.root.mainloop()
    finally:
        save_pet(pet)
