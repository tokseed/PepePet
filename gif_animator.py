import os
from PIL import Image, ImageTk


class GifAnimator:
    def __init__(self, label_widget):
        self.label = label_widget
        self.frames = []
        self.current_index = 0
        self.current_state = None
        self.animation_id = None

    def load_gif(self, state):
        """Загрузить GIF для состояния"""
        gif_path = f'assets/{state}.gif'

        if not os.path.exists(gif_path):
            # Если GIF нет - показываем эмодзи
            self.frames = []
            self.current_state = state
            return False

        try:
            gif = Image.open(gif_path)
            self.frames = []

            try:
                for frame_num in range(gif.n_frames):
                    gif.seek(frame_num)
                    frame_image = gif.copy().convert('RGBA')
                    frame_image = frame_image.resize((150, 150), Image.LANCZOS)
                    self.frames.append(ImageTk.PhotoImage(frame_image))
            except EOFError:
                pass

            self.current_index = 0
            self.current_state = state
            return True
        except Exception as e:
            print(f"Ошибка загрузки GIF {gif_path}: {e}")
            self.frames = []
            return False

    def animate(self):
        """Анимация GIF (вызывается циклично)"""
        if self.frames:
            self.label.config(image=self.frames[self.current_index], text='')
            self.current_index = (self.current_index + 1) % len(self.frames)
        return 100  # интервал в мс

    def show_emoji(self, emoji, font_size=80):
        """Показать эмодзи вместо GIF"""
        self.frames = []
        self.label.config(text=emoji, font=('Arial', font_size), image='')

    def has_frames(self):
        """Проверка наличия кадров"""
        return len(self.frames) > 0
