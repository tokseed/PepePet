import tkinter as tk
import random


class BiteOverlay:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return

        self.initialized = True
        self.window = tk.Toplevel()
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-transparentcolor', 'white')
        self.window.overrideredirect(True)

        self.canvas = tk.Canvas(self.window, bg='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        self.bites = []

    def add_bite(self, bite_count):
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        base_size = 150
        bite_size = base_size + (bite_count - 1) * 30

        x_start = screen_width - bite_size - 50
        y_start = screen_height - bite_size - 80

        self.create_jagged_square(x_start, y_start, bite_size)

    def create_jagged_square(self, x, y, size):
        points = []
        segments = 8

        for i in range(segments):
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-10, 10)
            points.append(x + (size * i / segments) + offset_x)
            points.append(y + offset_y)

        for i in range(segments):
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-15, 15)
            points.append(x + size + offset_x)
            points.append(y + (size * i / segments) + offset_y)

        for i in range(segments, 0, -1):
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-10, 10)
            points.append(x + (size * i / segments) + offset_x)
            points.append(y + size + offset_y)

        for i in range(segments, 0, -1):
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-15, 15)
            points.append(x + offset_x)
            points.append(y + (size * i / segments) + offset_y)

        bite = self.canvas.create_polygon(points, fill='black', outline='black')
        self.bites.append(bite)

    def clear_bites(self):
        for bite in self.bites:
            self.canvas.delete(bite)
        self.bites = []

    def destroy(self):
        if hasattr(self, 'window'):
            self.window.destroy()
            BiteOverlay._instance = None
