import os
import logging
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

log = logging.getLogger("image_display")

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif",".jfif", ".webp"]
IMAGES_FOLDER    = "images"


def find_image(word: str) -> str | None:
    for ext in IMAGE_EXTENSIONS:
        path = os.path.join(IMAGES_FOLDER, f"{word.lower()}{ext}")
        if os.path.exists(path):
            return path
    log.warning(f"No image found for '{word}' in '{IMAGES_FOLDER}/'")
    return None


class ImageDisplay:
    def __init__(self):
        self._root       = None
        self._label      = None
        self._thread     = None
        self._running    = False
        self._lock       = threading.Lock()
        self._next_image = None 

    def show(self, word: str):
        path = find_image(word)
        if path is None:
            log.warning(f"Skipping image display for '{word}', file not found.")
            return

        with self._lock:
            self._next_image = path

        if not self._running:
            self._start_window(path)
        else:
            if self._root:
                self._root.after(0, self._update_image)

    def close(self):
        if self._root:
            self._root.after(0, self._destroy)

    def _start_window(self, path: str):
        self._running = True
        self._thread  = threading.Thread(target=self._run_tk, args=(path,), daemon=True)
        self._thread.start()

    def _run_tk(self, initial_path: str):
        self._root = tk.Tk()
        self._root.title("Naming Task")
        self._root.configure(bg="white")

        # Fullscreen
        self._root.attributes("-fullscreen", True)
        self._root.attributes("-topmost", True)

        # Close fullscreen with Escape key
        self._root.bind("<Escape>", lambda e: self._destroy())

        # Image label
        self._label = tk.Label(self._root, bg="white")
        self._label.pack(expand=True, fill="both")

        # Show the first image
        self._load_and_display(initial_path)

        self._root.after(100, self._poll_for_updates)
        self._root.mainloop()
        self._running = False

    def _poll_for_updates(self):
        if not self._running:
            return
        with self._lock:
            path = self._next_image
            self._next_image = None

        if path:
            self._load_and_display(path)

        if self._running and self._root:
            self._root.after(100, self._poll_for_updates)

    def _update_image(self):
        with self._lock:
            path = self._next_image
            self._next_image = None
        if path:
            self._load_and_display(path)

    def _load_and_display(self, path: str):
        try:
            img = Image.open(path)

            screen_w = self._root.winfo_screenwidth()
            screen_h = self._root.winfo_screenheight()

            img_w, img_h = img.size
            scale = min(screen_w / img_w, screen_h / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            img   = img.resize((new_w, new_h), Image.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            self._label.configure(image=photo)
            self._label.image = photo 
            log.info(f"Displaying image: {path}")

        except Exception as e:
            log.error(f"Failed to load image '{path}': {e}")

    def _destroy(self):
        self._running = False
        if self._root:
            self._root.quit()
            self._root.destroy()
            self._root  = None
            self._label = None
