import threading
import tkinter as tk
from tkinter import ttk
from typing import List, Tuple

from app.capture.detector import list_cameras, format_camera_label
from app.config.schema import SharedState


class CameraManagerGUI:
    def __init__(self, shared: SharedState):
        self.shared = shared
        self.root = tk.Tk()
        self.root.title("Booth Camera Manager")
        self.root.geometry("520x260")

        self._build()
        self._populate()

    def _build(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Available Cameras:").pack(anchor=tk.W)
        self.combo = ttk.Combobox(frm, state="readonly", width=70)
        self.combo.pack(fill=tk.X, pady=6)

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X, pady=6)
        self.refresh_btn = ttk.Button(btns, text="Refresh", command=self._populate)
        self.refresh_btn.pack(side=tk.LEFT)
        self.apply_btn = ttk.Button(btns, text="Apply", command=self._apply)
        self.apply_btn.pack(side=tk.LEFT, padx=8)

        self.status = ttk.Label(frm, text="", foreground="#555")
        self.status.pack(anchor=tk.W, pady=(10, 0))

    def _populate(self):
        cams = list_cameras(max_index=20)
        self.entries: List[Tuple[int, int]] = []  # (index, backend)
        labels: List[str] = []
        for c in cams:
            self.entries.append((c["index"], c["backend"]))
            labels.append(format_camera_label(c))
        if not labels:
            labels = ["No cameras found"]
        self.combo["values"] = labels
        if labels:
            self.combo.current(0)
        self.status.config(text=f"Found {len(self.entries)} camera(s)")

    def _apply(self):
        if not getattr(self, "entries", None):
            return
        sel = self.combo.current()
        if sel < 0 or sel >= len(self.entries):
            return
        idx, backend = self.entries[sel]
        # Write into shared params; the main loop will hot-swap
        self.shared.set_param("capture.source", int(idx))
        self.shared.set_param("capture.backend", int(backend))
        self.status.config(text=f"Selected index {idx} (backend {backend})")

    def run(self):
        self.root.mainloop()


def run_manager_gui(shared: SharedState):
    gui = CameraManagerGUI(shared)
    gui.run()
