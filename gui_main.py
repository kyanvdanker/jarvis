import customtkinter as ctk
import tkinter as tk
import math
import time
import os

# -------------------------
# THEME CONFIG
# -------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG_MAIN = "#0D1B2A"
BG_PANEL = "#1B263B"
ACCENT = "#00A8E8"
TEXT = "#E0E0E0"


class JarvisUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("J.A.R.V.I.S")
        self.root.after(10, lambda: self.root.state("zoomed"))
        self.root.configure(fg_color=BG_MAIN)

        # Screen size
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        # Dynamic font sizes
        font_small = int(screen_h * 0.015)
        font_medium = int(screen_h * 0.02)
        font_large = int(screen_h * 0.03)

        # -------------------------
        # TOP BAR
        # -------------------------
        self.top_bar = ctk.CTkFrame(self.root, fg_color=BG_PANEL, height=int(screen_h * 0.06))
        self.top_bar.pack(fill="x", side="top")

        self.status_label = ctk.CTkLabel(
            self.top_bar,
            text="J.A.R.V.I.S (Online)",
            text_color=ACCENT,
            font=("Segoe UI", font_medium, "bold")
        )
        self.status_label.pack(side="left", padx=20)

        self.time_label = ctk.CTkLabel(
            self.top_bar,
            text="",
            text_color=TEXT,
            font=("Segoe UI", font_small)
        )
        self.time_label.pack(side="right", padx=20)
        self.update_time()

        # -------------------------
        # MAIN FRAME
        # -------------------------
        self.main_frame = ctk.CTkFrame(self.root, fg_color=BG_MAIN)
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.pack_propagate(False)

        # -------------------------
        # NEON RING CANVAS
        # -------------------------
        canvas_size = int(screen_h * 0.35)

        self.canvas = tk.Canvas(
            self.main_frame,
            width=canvas_size,
            height=canvas_size,
            bg=BG_MAIN,
            highlightthickness=0
        )
        self.canvas.place(x=screen_w * 0.03, y=screen_h * 0.05)

        self.ring_radius = int(canvas_size * 0.36)
        self.ring_color = ACCENT
        self.pulse = 0
        self.listening = False

        # -------------------------
        # FILE VIEWER
        # -------------------------
        self.file_viewer = ctk.CTkTextbox(
            self.main_frame,
            fg_color=BG_PANEL,
            text_color=TEXT,
            font=("Segoe UI", font_small),
            wrap="word",
            width=int(screen_w * 0.6),
            height=int(screen_h * 0.20)
        )
        self.file_viewer.place(x=screen_w * 0.03, y=screen_h * 0.45)
        self.file_viewer.configure(state="disabled")

        # -------------------------
        # CHAT BOX
        # -------------------------
        self.chat_box = ctk.CTkTextbox(
            self.main_frame,
            fg_color=BG_PANEL,
            text_color=TEXT,
            font=("Segoe UI", font_small),
            wrap="word",
            width=int(screen_w * 0.6),
            height=int(screen_h * 0.25)
        )
        self.chat_box.place(x=screen_w * 0.03, y=screen_h * 0.70)
        self.chat_box.configure(state="disabled")

        # -------------------------
        # SIDEBAR
        # -------------------------
        self.sidebar = ctk.CTkFrame(
            self.main_frame,
            fg_color=BG_PANEL,
            width=int(screen_w * 0.22),
            height=int(screen_h * 0.85)
        )
        self.sidebar.place(x=screen_w * 0.73, y=screen_h * 0.05)

        # PROJECTS
        self.project_label = ctk.CTkLabel(
            self.sidebar, text="Projects", text_color=ACCENT, font=("Segoe UI", font_medium, "bold")
        )
        self.project_label.pack(pady=(15, 5))

        self.project_list = ctk.CTkTextbox(
            self.sidebar, fg_color=BG_MAIN, text_color=TEXT, height=int(screen_h * 0.12)
        )
        self.project_list.pack(fill="x", padx=12)

        # FILES
        self.file_label = ctk.CTkLabel(
            self.sidebar, text="Files", text_color=ACCENT, font=("Segoe UI", font_medium, "bold")
        )
        self.file_label.pack(pady=(15, 5))

        self.file_list = ctk.CTkTextbox(
            self.sidebar, fg_color=BG_MAIN, text_color=TEXT, height=int(screen_h * 0.12)
        )
        self.file_list.pack(fill="x", padx=12)

        # MEMORY
        self.memory_label = ctk.CTkLabel(
            self.sidebar, text="Memory", text_color=ACCENT, font=("Segoe UI", font_medium, "bold")
        )
        self.memory_label.pack(pady=(15, 5))

        self.memory_list = ctk.CTkTextbox(
            self.sidebar, fg_color=BG_MAIN, text_color=TEXT, height=int(screen_h * 0.12)
        )
        self.memory_list.pack(fill="x", padx=12)

        # TIMELINE
        self.timeline_label = ctk.CTkLabel(
            self.sidebar, text="Timeline", text_color=ACCENT, font=("Segoe UI", font_medium, "bold")
        )
        self.timeline_label.pack(pady=(15, 5))

        self.timeline_box = ctk.CTkTextbox(
            self.sidebar, fg_color=BG_MAIN, text_color=TEXT, height=int(screen_h * 0.20)
        )
        self.timeline_box.pack(fill="both", expand=True, padx=12, pady=(0, 15))

        # Start animation loop
        self.animate_ring()

    # -------------------------
    # RING ANIMATION
    # -------------------------
    def animate_ring(self):
        self.canvas.delete("all")

        pulse_strength = 14 if self.listening else 5
        pulse = pulse_strength + math.sin(self.pulse) * (pulse_strength * 0.7)

        center = self.canvas.winfo_width() // 2

        # Outer glow
        self.canvas.create_oval(
            center - self.ring_radius - pulse,
            center - self.ring_radius - pulse,
            center + self.ring_radius + pulse,
            center + self.ring_radius + pulse,
            outline=self.ring_color,
            width=3
        )

        # Main neon ring
        self.canvas.create_oval(
            center - self.ring_radius,
            center - self.ring_radius,
            center + self.ring_radius,
            center + self.ring_radius,
            outline=self.ring_color,
            width=6
        )

        # Inner ring
        self.canvas.create_oval(
            center - (self.ring_radius - 25),
            center - (self.ring_radius - 25),
            center + (self.ring_radius - 25),
            center + (self.ring_radius - 25),
            outline="#0088cc",
            width=2
        )

        # Center text
        self.canvas.create_text(
            center, center,
            text="J.A.R.V.I.S",
            fill=self.ring_color,
            font=("Segoe UI", int(self.canvas.winfo_height() * 0.08), "bold")
        )

        self.pulse += 0.10
        self.root.after(16, self.animate_ring)

    # -------------------------
    # TIME DISPLAY
    # -------------------------
    def update_time(self):
        now = time.strftime("%H:%M:%S | %B %d, %Y")
        self.time_label.configure(text=now)
        self.root.after(1000, self.update_time)

    # -------------------------
    # CHAT OUTPUT
    # -------------------------
    def add_message(self, sender, text):
        def _update():
            self.chat_box.configure(state="normal")
            self.chat_box.insert("end", f"{sender}: {text}\n")
            self.chat_box.configure(state="disabled")
            self.chat_box.see("end")
        self.root.after(0, _update)

    # -------------------------
    # PROJECT + FILE LISTS
    # -------------------------
    def update_projects(self, projects):
        self.project_list.configure(state="normal")
        self.project_list.delete("1.0", "end")
        for p in projects:
            self.project_list.insert("end", p + "\n")
        self.project_list.configure(state="disabled")

    def update_files(self, files):
        self.file_list.configure(state="normal")
        self.file_list.delete("1.0", "end")
        for f in files:
            self.file_list.insert("end", f + "\n")
        self.file_list.configure(state="disabled")

    # -------------------------
    # FILE VIEWER
    # -------------------------
    def open_file(self, path):
        self.file_viewer.configure(state="normal")
        self.file_viewer.delete("1.0", "end")

        ext = os.path.splitext(path)[1].lower()

        try:
            if ext in [".txt", ".md", ".log", ".py", ".json", ".csv"]:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                self.file_viewer.insert("end", content)
            else:
                self.file_viewer.insert("end", f"Cannot preview this file type: {ext}")

        except Exception as e:
            self.file_viewer.insert("end", f"Error opening file:\n{e}")

        self.file_viewer.configure(state="disabled")

    # -------------------------
    # MAIN LOOP
    # -------------------------
    def run(self):
        self.root.mainloop()


# Global instance
ui = JarvisUI()

def set_projects(projects):
    ui.update_projects(projects)

def set_files(files):
    ui.update_files(files)

def update_memory(items):
    try:
        ui.root.after(0, lambda: _update_memory(items))
    except Exception:
        pass

def update_timeline(text):
    try:
        ui.root.after(0, lambda: _update_timeline(text))
    except Exception:
        pass

def open_file_in_gui(path):
    try:
        ui.root.after(0, lambda: ui.open_file(path))
    except Exception:
        pass


def _update_memory(items):
    ui.memory_list.configure(state="normal")
    ui.memory_list.delete("1.0", "end")
    for item in items:
        ui.memory_list.insert("end", item + "\n")
    ui.memory_list.configure(state="disabled")


def _update_timeline(text):
    ui.timeline_box.configure(state="normal")
    ui.timeline_box.delete("1.0", "end")
    ui.timeline_box.insert("end", text)
    ui.timeline_box.configure(state="disabled")
