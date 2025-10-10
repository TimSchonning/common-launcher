import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

CONFIG_FILE = "games.json"
IMAGES_DIR = "images"
ICON_SIZE = (96, 96)

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
        self.geometry("800x600")
        ensure_dirs()
        self.config_data = load_config()
        self.icons_cache = {}  # path -> PhotoImage
        self.create_widgets()
        self.populate()

    def create_widgets(self):
        top = tk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X)

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(top, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=6, pady=6, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.populate())

        # Scrollable canvas for grid
        self.canvas = tk.Canvas(self)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def populate(self):
        # Clear current widgets
        for w in self.frame.winfo_children():
            w.destroy()

        q = self.search_var.get().strip().lower()
        filtered = [g for g in self.config_data if q in g.get("name", "").lower()]

        cols = 4
        row = col = 0
        for g in filtered:
            card = tk.Frame(self.frame, bd=1, relief=tk.RAISED, padx=8, pady=8)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="n")
            # Icon
            icon = self.get_icon_for_game(g)
            if icon:
                lbl = tk.Label(card, image=icon)
                lbl.image = icon
                lbl.pack()
            else:
                lbl = tk.Label(card, width=ICON_SIZE[0]//8, height=6, text="No Image")
                lbl.pack()

            name = g.get("name", "Unnamed")
            tk.Label(card, text=name, wraplength=120).pack(pady=(6, 2))
            btn_frame = tk.Frame(card)
            btn_frame.pack(fill=tk.X)
            launch_btn = tk.Button(btn_frame, text="Play", command=lambda p=g["path"]: self.launch(p))
            launch_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
            edit_btn = tk.Button(btn_frame, text="Edit", command=lambda g=g: self.edit_game_dialog(g))
            edit_btn.pack(side=tk.LEFT, padx=4)
            rm_btn = tk.Button(btn_frame, text="Remove", command=lambda g=g: self.remove_game(g))
            rm_btn.pack(side=tk.LEFT)

            col += 1
            if col >= cols:
                col = 0
                row += 1

    def get_icon_for_game(self, game):
        img_path = game.get("image")
        if img_path:
            # absolute-ify relative images saved in images/
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
            # Use list form to avoid shell parsing issues
            # For windows .exe, this will start the program and return immediately
            subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
        except Exception as e:
            messagebox.showerror("Launch failed", str(e))

def main():
    # Ensure config exists (create empty if not)
    if not os.path.exists(CONFIG_FILE):
        save_config([])

    app = LauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
