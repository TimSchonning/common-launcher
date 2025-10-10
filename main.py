import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

CONFIG_FILE = "games.json"
IMAGES_DIR = "images"
ICON_SIZE = (220, 220)
background_colour = "#1A1A1A"
card_colour = "#313131"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return []
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def ensure_dirs():
    if not os.path.isdir(IMAGES_DIR):
        os.makedirs(IMAGES_DIR, exist_ok=True)

def make_thumbnail(image_path):
    try:
        img = Image.open(image_path)
        img.thumbnail(ICON_SIZE, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Game Launcher")
        self.geometry("1080x1920")
        self.attributes("-fullscreen", True)
        self.configure(bg=background_colour)
        ensure_dirs()
        self.config_data = load_config()
        self.icons_cache = {}
        self.create_widgets()
        self.populate()

    def create_widgets(self):
        self.search_var = tk.StringVar()

        self.margin_frame = tk.Frame(self, bg=background_colour)
        self.margin_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=50, pady=50)

        self.canvas = tk.Canvas(self.margin_frame, bg=background_colour, highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.frame = tk.Frame(self.canvas, bg=background_colour)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        exit_btn = tk.Button(self, text="Exit", font=("Segoe UI", 20, "bold"), command=self.destroy, pady=10, padx=20)
        exit_btn.pack(side=tk.BOTTOM, pady=20, padx=20)


    def populate(self):
        for w in self.frame.winfo_children():
            w.destroy()

        q = self.search_var.get().strip().lower()
        filtered = [g for g in self.config_data if q in g.get("name", "").lower()]

        # --- Determine screen width and scaling ---
        screen_width = self.winfo_width() or 1080
        cols = max(10, min(10, screen_width // 260))
        base_card_width = screen_width / cols - 40
        card_width = int(base_card_width)
        card_height = int(card_width * 1.5)

        # --- Scalable font sizes ---
        name_font_size = max(24, int(card_width / 15))
        desc_font_size = max(14, int(card_width / 22))
        btn_font_size = max(14, int(card_width / 18))

        row = col = 0

        for g in filtered:
            card = tk.Frame(
                self.frame,
                width=card_width,
                height=card_height,
                bd=0,
                relief=tk.RAISED,
                padx=int(card_width * 0.2),
                pady=int(card_height * 0.2),
                bg=card_colour,
            )
            card.grid(row=row, column=col, padx=20, pady=20, sticky="n")
            card.grid_propagate(False)

            # --- Icon ---
            icon = self.get_icon_for_game(g)
            if icon:
                lbl = tk.Label(card, image=icon, bg=card_colour, bd=0, highlightthickness=0)
                lbl.image = icon
                lbl.pack(padx=20, pady=(10, 15))
            else:
                lbl = tk.Label(
                    card,
                    text="No Image",
                    bg=card_colour,
                    fg="white",
                    width=int(card_width / 20),
                    height=int(card_height / 100),
                )
                lbl.pack(padx=20, pady=(10, 15))

            # --- Game name ---
            name = g.get("name", "Unnamed")
            tk.Label(
                card,
                text=name,
                wraplength=card_width - 40,
                font=("Segoe UI", name_font_size, "bold"),
                bg=card_colour,
                fg="white",
            ).pack(pady=(5, 5))

            # --- Description ---
            desc = g.get("desc", "")
            tk.Label(
                card,
                text=desc,
                wraplength=card_width - 40,
                font=("Segoe UI", desc_font_size),
                bg=card_colour,
                fg="white",
            ).pack(pady=(0, 10))

            # --- Launch button ---
            btn_frame = tk.Frame(card, bg=card_colour)
            btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
            launch_btn = tk.Button(
                btn_frame,
                text="Start",
                fg="black",
                font=("Segoe UI", btn_font_size, "bold"),
                bg="#09ff68",
                command=lambda p=g["path"]: self.launch(p),
            )
            launch_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)

            col += 1
            if col >= cols:
                col = 0
                row += 1


    def get_icon_for_game(self, game):
        img_path = game.get("image")
        if img_path:
            if not os.path.isabs(img_path):
                img_path = os.path.join(IMAGES_DIR, img_path)
        if not img_path or not os.path.exists(img_path):
            return None
        if img_path in self.icons_cache:
            return self.icons_cache[img_path]
        thumb = make_thumbnail(img_path)
        if thumb:
            self.icons_cache[img_path] = thumb
        return thumb

    def launch(self, exe_path):
        if not os.path.exists(exe_path):
            messagebox.showerror("Executable not found", f"Path doesn't exist:\n{exe_path}")
            return
        try:
            subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
        except Exception as e:
            messagebox.showerror("Launch failed", str(e))

def main():
    if not os.path.exists(CONFIG_FILE):
        save_config([])

    app = LauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
