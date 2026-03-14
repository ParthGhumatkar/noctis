from __future__ import annotations

import ctypes
import json
import threading
from dataclasses import dataclass
from pathlib import Path
from tkinter import Button, Frame, Label, Menu, Scrollbar, Text, filedialog
from PIL import Image, ImageTk
from typing import Callable, Dict, List, Optional

import customtkinter as ctk
import requests

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Colors
BG        = "#0f1410"   # window / menu / tab bar
BG_EDIT   = "#111911"   # editor background
BG_TAB    = "#0f1410"   # same as BG (kept for compatibility)
BG_DARK   = "#0a0f0a"   # status bar
FG        = "#e8e0cc"   # active / UI text
FG_EDITOR = "#d8d0bc"   # editor body text
FG_DIM    = "#5a6a5a"   # inactive / dim text
ACCENT    = "#7ab648"   # green accent
ACCENT_D  = "#1e3a1e"   # deep green (selection, separator)
TAB_ACTIVE = "#1e2920"  # active tab background
FONT      = ("Consolas", 13)

AI_URL = "http://localhost:11434/api/generate"
AI_CHAT_URL = "http://localhost:11434/api/chat"
AI_MODEL = "phi3:mini"

NOCTIS_SYSTEM_PROMPT = (
    "You are Noctis, a warm and private AI companion running 100% locally on this "
    "device. No internet. No data leaves this machine. You are embedded in a private "
    "mental health notepad. Be calm, warm, concise and non-judgmental. Never mention "
    "being a cloud service or having internet access. You are fully local and private."
)

_AI_SEP = "─────────────────────────────"


def stream_ollama(
    prompt: str,
    history: List[Dict[str, str]],
    on_token: Callable[[str], None],
    on_done: Callable[[str], None],
    on_error: Callable[[], None],
) -> None:
    """Send a chat request to Ollama with streaming=True.
    Calls on_token(token) for each chunk, on_done(full_reply) at the end,
    or on_error() if the request fails."""
    def run() -> None:
        try:
            messages = history + [{"role": "user", "content": prompt}]
            full_reply = ""
            with requests.post(
                AI_CHAT_URL,
                json={
                    "model": AI_MODEL,
                    "messages": messages,
                    "stream": True,
                },
                stream=True,
                timeout=300,
            ) as r:
                for raw_line in r.iter_lines():
                    if not raw_line:
                        continue
                    chunk = json.loads(raw_line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        full_reply += token
                        on_token(token)
                    if chunk.get("done"):
                        break
            on_done(full_reply)
        except Exception:
            on_error()

    threading.Thread(target=run, daemon=True).start()


@dataclass
class TabInfo:
    frame: Frame
    button: Button
    close_button: Button
    indicator: Frame
    text: Text
    file_path: Optional[Path]
    title: str
    unsaved: bool = False


def dark_titlebar(window) -> None:
    window.update()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
    value = ctypes.c_int(1)
    set_window_attribute(
        hwnd,
        DWMWA_USE_IMMERSIVE_DARK_MODE,
        ctypes.byref(value),
        ctypes.sizeof(value),
    )


class Noctis(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Noctis")
        self.geometry("1100x720")
        self.minsize(800, 550)
        self.configure(fg_color=BG)

        self.tk_setPalette(background=BG, foreground=FG)

        self.font_family = "Consolas"
        self.font_size = 13

        self.tabs: List[TabInfo] = []
        self.current_tab_index: Optional[int] = None

        self._ai_mode: bool = False
        self._ai_chat_history: List[Dict[str, str]] = []
        self._images: List[ImageTk.PhotoImage] = []

        self._create_widgets()
        self._create_keybindings()

        self.new_tab()
        dark_titlebar(self)

    def _create_widgets(self) -> None:
        menubar = Menu(self, tearoff=0)
        menubar.config(
            bg=BG,
            fg="#8a9a8a",
            activebackground=TAB_ACTIVE,
            activeforeground=FG,
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        self.configure(menu=menubar)

        _menu_cfg = {
            "bg": BG,
            "fg": "#8a9a8a",
            "activebackground": TAB_ACTIVE,
            "activeforeground": FG,
            "borderwidth": 0,
            "font": ("Segoe UI", 9),
        }

        file_menu = Menu(menubar, tearoff=0)
        file_menu.config(**_menu_cfg)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Tab", command=self.new_tab)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)

        edit_menu = Menu(menubar, tearoff=0)
        edit_menu.config(**_menu_cfg)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._editor_undo)
        edit_menu.add_command(label="Redo", command=self._editor_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self._editor_cut)
        edit_menu.add_command(label="Copy", command=self._editor_copy)
        edit_menu.add_command(label="Paste", command=self._editor_paste)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self._editor_select_all)
        edit_menu.add_command(label="Find & Replace", command=self.open_find_replace)

        format_menu = Menu(menubar, tearoff=0)
        format_menu.config(**_menu_cfg)
        menubar.add_cascade(label="Format", menu=format_menu)
        format_menu.add_command(label="Font", command=self.open_font_picker)
        format_menu.add_command(label="Word Wrap", command=self.toggle_word_wrap)
        format_menu.add_separator()
        format_menu.add_command(
            label="Insert Image  Ctrl+Shift+I",
            command=self.insert_image,
        )

        ai_menu = Menu(menubar, tearoff=0)
        ai_menu.config(**_menu_cfg)
        menubar.add_cascade(label="AI", menu=ai_menu)
        ai_menu.add_command(label="Ask AI", command=self.ask_ai)
        ai_menu.add_command(label="Summarize", command=self.summarize_note)
        ai_menu.add_command(label="Fix Grammar", command=self.fix_grammar)

        help_menu = Menu(menubar, tearoff=0)
        help_menu.config(**_menu_cfg)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        # ── Tab bar ──────────────────────────────────────────────────────────
        self.tabs_bar = Frame(self, bg=BG)
        self.tabs_bar.pack(side="top", fill="x")

        # Right-side buttons packed first so they stay on far right
        self.ai_toggle_btn = Button(
            self.tabs_bar,
            text="AI",
            bg="#1a2a1a",
            fg=FG_DIM,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            activebackground=ACCENT,
            activeforeground=BG,
            bd=0,
            command=self.toggle_ai,
        )
        self.ai_toggle_btn.pack(side="right", padx=(2, 8), pady=4)

        self.new_tab_button = Button(
            self.tabs_bar,
            text="+",
            bg=BG,
            fg=ACCENT,
            font=("Segoe UI", 14),
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2,
            activebackground=TAB_ACTIVE,
            activeforeground=FG,
            bd=0,
            command=self.new_tab,
        )
        self.new_tab_button.pack(side="right", padx=2, pady=4)

        # Tabs row (left side of bar)
        self.tabs_container = Frame(self.tabs_bar, bg=BG)
        self.tabs_container.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # 1px separator below tab bar
        Frame(self, bg="#1a2a1a", height=1).pack(side="top", fill="x")

        # ── Status bar (packed bottom-up before editor) ───────────────────────
        self.statusbar = Frame(self, bg=BG_DARK)
        self.statusbar.pack(side="bottom", fill="x")

        # 1px separator above status bar
        Frame(self, bg="#1a2a1a", height=1).pack(side="bottom", fill="x")

        self.status_label = Label(
            self.statusbar,
            text="Ln 1  Col 1  |  0 words",
            bg=BG_DARK,
            fg="#3d5c1e",
            font=("Segoe UI", 8),
            padx=16,
            pady=3,
        )
        self.status_label.pack(side="left")

        Label(
            self.statusbar,
            text=f"\U0001f512 Local  |  {AI_MODEL}",
            bg=BG_DARK,
            fg="#3d5c1e",
            font=("Segoe UI", 8),
            padx=16,
            pady=3,
        ).pack(side="right")

        # ── Editor container (fills remaining space) ──────────────────────────
        self.editor_container = Frame(self, bg=BG_EDIT)
        self.editor_container.pack(fill="both", expand=True)

    def new_tab(self, file_path: Optional[Path] = None, content: str = "") -> None:
        title = file_path.name if file_path else "Untitled"

        tab_frame = Frame(self.editor_container, bg=BG_EDIT)

        text_widget = Text(
            tab_frame,
            bg=BG_EDIT,
            fg=FG_EDITOR,
            insertbackground=ACCENT,
            selectbackground=ACCENT_D,
            selectforeground=FG,
            font=(self.font_family, self.font_size),
            wrap="word",
            relief="flat",
            bd=0,
            padx=32,
            pady=24,
            spacing1=3,
            spacing2=0,
            spacing3=3,
            cursor="xterm",
        )
        scrollbar = Scrollbar(
            tab_frame,
            bg=BG_DARK,
            troughcolor=BG,
            activebackground="#3d5c1e",
            highlightthickness=0,
            relief="flat",
            width=6,
            bd=0,
        )
        text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=text_widget.yview)

        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True)

        text_widget.insert("1.0", content)
        text_widget.edit_modified(False)

        self._ensure_ai_tags(text_widget)
        text_widget.bind("<<Modified>>", self._on_text_modified)
        text_widget.bind("<KeyRelease>", self._update_status_from_event)
        text_widget.bind("<ButtonRelease>", self._update_status_from_event)
        text_widget.bind("<Control-v>", self._paste_handler)
        text_widget.bind("<Control-V>", self._paste_handler)
        text_widget.bind("<Return>", self._handle_enter)

        tab_button_frame = Frame(self.tabs_container, bg=BG)
        tab_button_frame.pack(side="left", padx=(0, 1))

        # 2px top indicator line — green when active, invisible (same as BG) when not
        indicator = Frame(tab_button_frame, bg=BG, height=2)
        indicator.pack(side="top", fill="x")

        tab_button = Button(
            tab_button_frame,
            text=self._truncate(title),
            bg=BG,
            fg=FG_DIM,
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=5,
            activebackground=TAB_ACTIVE,
            activeforeground=FG,
            anchor="w",
            bd=0,
            command=lambda idx=len(self.tabs): self.switch_tab(idx),
        )
        tab_button.pack(side="left")

        close_button = Button(
            tab_button_frame,
            text="×",
            bg=BG,
            fg=FG_DIM,
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=4,
            pady=5,
            activebackground=TAB_ACTIVE,
            activeforeground="#ff4455",
            bd=0,
            command=lambda idx=len(self.tabs): self.close_tab(idx),
        )
        close_button.bind("<Enter>", lambda e: close_button.config(fg="#ff4455"))
        close_button.bind("<Leave>", lambda e: close_button.config(fg=FG_DIM))
        # Close button starts hidden; shown only when tab is active

        tab_info = TabInfo(
            frame=tab_frame,
            button=tab_button,
            close_button=close_button,
            indicator=indicator,
            text=text_widget,
            file_path=file_path,
            title=title,
            unsaved=bool(content),
        )
        self.tabs.append(tab_info)

        self.switch_tab(len(self.tabs) - 1)

    def switch_tab(self, index: int) -> None:
        if index < 0 or index >= len(self.tabs):
            return

        if self.current_tab_index is not None:
            current = self.tabs[self.current_tab_index]
            current.frame.pack_forget()
            current.button.config(bg=BG, fg=FG_DIM)
            current.button.master.config(bg=BG)
            current.indicator.config(bg=BG)
            current.close_button.pack_forget()

        self.current_tab_index = index
        tab = self.tabs[index]
        tab.frame.pack(fill="both", expand=True)
        tab.button.config(bg=TAB_ACTIVE, fg=FG)
        tab.button.master.config(bg=TAB_ACTIVE)
        tab.indicator.config(bg=ACCENT)
        tab.close_button.config(bg=TAB_ACTIVE, fg=FG_DIM)
        tab.close_button.pack(side="left", padx=(0, 6))
        self._update_status()

    def close_tab(self, index: Optional[int] = None) -> None:
        if not self.tabs:
            return

        if index is None:
            index = self.current_tab_index
        if index is None or index < 0 or index >= len(self.tabs):
            return

        tab = self.tabs[index]
        if tab.unsaved:
            if not self._confirm_discard_changes(tab.title):
                return

        tab.frame.destroy()
        tab.button.master.destroy()

        del self.tabs[index]

        if not self.tabs:
            self.current_tab_index = None
            self.new_tab()
            return

        if index >= len(self.tabs):
            index = len(self.tabs) - 1
        self.current_tab_index = None
        self.switch_tab(index)

    def _get_current_tab(self) -> Optional[TabInfo]:
        if self.current_tab_index is None:
            return None
        if not (0 <= self.current_tab_index < len(self.tabs)):
            return None
        return self.tabs[self.current_tab_index]

    def open_file(self) -> None:
        file_path_str = filedialog.askopenfilename(
            title="Open Note",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path_str:
            return

        path = Path(file_path_str)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return

        self.new_tab(file_path=path, content=content)

    def save_file(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return
        if tab.file_path is None:
            self.save_file_as()
            return
        self._write_tab_to_path(tab, tab.file_path)

    def save_file_as(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return

        file_path_str = filedialog.asksaveasfilename(
            title="Save Note As",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path_str:
            return

        path = Path(file_path_str)
        self._write_tab_to_path(tab, path)

    def _write_tab_to_path(self, tab: TabInfo, path: Path) -> None:
        content = tab.text.get("1.0", "end-1c")
        try:
            path.write_text(content, encoding="utf-8")
        except OSError:
            return

        tab.file_path = path
        tab.title = path.name
        tab.unsaved = False
        self._update_tab_title(tab)

    def _editor_undo(self) -> None:
        tab = self._get_current_tab()
        if tab:
            try:
                tab.text.edit_undo()
            except Exception:
                pass

    def _editor_redo(self) -> None:
        tab = self._get_current_tab()
        if tab:
            try:
                tab.text.edit_redo()
            except Exception:
                pass

    def _editor_cut(self) -> None:
        tab = self._get_current_tab()
        if tab:
            try:
                tab.text.event_generate("<<Cut>>")
            except Exception:
                pass

    def _editor_copy(self) -> None:
        tab = self._get_current_tab()
        if tab:
            try:
                tab.text.event_generate("<<Copy>>")
            except Exception:
                pass

    def _editor_paste(self) -> None:
        tab = self._get_current_tab()
        if tab:
            try:
                tab.text.event_generate("<<Paste>>")
            except Exception:
                pass

    def _editor_select_all(self) -> None:
        tab = self._get_current_tab()
        if tab:
            tab.text.tag_add("sel", "1.0", "end-1c")
            tab.text.focus_set()

    def open_find_replace(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return

        win = ctk.CTkToplevel(self)
        win.title("Find & Replace")
        win.configure(fg_color=BG_EDIT)
        win.resizable(False, False)

        ctk.CTkLabel(win, text="Find", text_color=FG).grid(
            row=0, column=0, padx=10, pady=(12, 4), sticky="w"
        )
        find_entry = ctk.CTkEntry(
            win,
            fg_color=BG_DARK,
            text_color=FG,
            border_color=ACCENT,
            corner_radius=8,
            width=260,
        )
        find_entry.grid(row=0, column=1, padx=10, pady=(12, 4), sticky="ew")

        ctk.CTkLabel(win, text="Replace", text_color=FG).grid(
            row=1, column=0, padx=10, pady=4, sticky="w"
        )
        replace_entry = ctk.CTkEntry(
            win,
            fg_color=BG_DARK,
            text_color=FG,
            border_color=ACCENT,
            corner_radius=8,
            width=260,
        )
        replace_entry.grid(row=1, column=1, padx=10, pady=4, sticky="ew")

        buttons_frame = ctk.CTkFrame(win, fg_color="transparent", corner_radius=0)
        buttons_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(8, 12), sticky="e")

        def do_find_next() -> None:
            pattern = find_entry.get()
            if pattern:
                self._find_text(pattern, forward=True)

        def do_find_prev() -> None:
            pattern = find_entry.get()
            if pattern:
                self._find_text(pattern, forward=False)

        def do_replace() -> None:
            pattern = find_entry.get()
            replacement = replace_entry.get()
            if pattern:
                self._replace_current(pattern, replacement)

        def do_replace_all() -> None:
            pattern = find_entry.get()
            replacement = replace_entry.get()
            if pattern:
                self._replace_all(pattern, replacement)

        for idx, (label, cmd) in enumerate(
            [
                ("Next", do_find_next),
                ("Previous", do_find_prev),
                ("Replace", do_replace),
                ("Replace All", do_replace_all),
            ]
        ):
            btn = ctk.CTkButton(
                buttons_frame,
                text=label,
                fg_color=ACCENT,
                hover_color=ACCENT,
                text_color=BG,
                corner_radius=8,
                command=cmd,
                width=100,
            )
            btn.grid(row=0, column=idx, padx=4, pady=4)

        win.grid_columnconfigure(1, weight=1)
        find_entry.focus_set()

    def _find_text(self, pattern: str, forward: bool = True) -> None:
        tab = self._get_current_tab()
        if not tab:
            return
        text = tab.text
        text.tag_remove("search_highlight", "1.0", "end")

        if forward:
            idx = text.search(pattern, "insert", stopindex="end")
        else:
            idx = text.search(pattern, "1.0", stopindex="insert", backwards=True)

        if not idx:
            return

        end_idx = f"{idx}+{len(pattern)}c"
        text.tag_add("search_highlight", idx, end_idx)
        text.tag_config(
            "search_highlight",
            background="#3d5c1e",
            foreground=FG,
        )
        text.mark_set("insert", end_idx if forward else idx)
        text.see(idx)

    def _replace_current(self, pattern: str, replacement: str) -> None:
        tab = self._get_current_tab()
        if not tab:
            return
        text = tab.text
        start = text.search(pattern, "insert", stopindex="end")
        if not start:
            return
        end = f"{start}+{len(pattern)}c"
        text.delete(start, end)
        text.insert(start, replacement)
        text.mark_set("insert", f"{start}+{len(replacement)}c")
        self._mark_unsaved(tab)

    def _replace_all(self, pattern: str, replacement: str) -> None:
        tab = self._get_current_tab()
        if not tab:
            return
        text = tab.text
        pos = "1.0"
        while True:
            idx = text.search(pattern, pos, stopindex="end")
            if not idx:
                break
            end = f"{idx}+{len(pattern)}c"
            text.delete(idx, end)
            text.insert(idx, replacement)
            pos = f"{idx}+{len(replacement)}c"
        self._mark_unsaved(tab)

    def open_font_picker(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return

        win = ctk.CTkToplevel(self)
        win.title("Font Picker")
        win.configure(fg_color=BG_EDIT)
        win.resizable(False, False)

        ctk.CTkLabel(win, text="Font Family", text_color=FG).grid(
            row=0, column=0, padx=12, pady=(12, 4), sticky="w"
        )

        font_families = ["Consolas", "Cascadia Code", "Fira Code", "JetBrains Mono"]
        if self.font_family not in font_families:
            font_families.insert(0, self.font_family)

        font_var = ctk.StringVar(value=self.font_family)
        font_dropdown = ctk.CTkOptionMenu(
            win,
            values=font_families,
            variable=font_var,
            fg_color=BG_DARK,
            button_color=ACCENT_D,
            button_hover_color=ACCENT,
            text_color=FG,
        )
        font_dropdown.grid(row=0, column=1, padx=12, pady=(12, 4), sticky="ew")

        ctk.CTkLabel(win, text="Size", text_color=FG).grid(
            row=1, column=0, padx=12, pady=4, sticky="w"
        )

        size_var = ctk.IntVar(value=self.font_size)
        size_slider = ctk.CTkSlider(
            win,
            from_=10,
            to=24,
            number_of_steps=14,
            fg_color="#2d3d2d",
            progress_color=ACCENT,
            button_color=ACCENT,
            variable=size_var,
        )
        size_slider.grid(row=1, column=1, padx=12, pady=4, sticky="ew")

        size_label = ctk.CTkLabel(win, text=str(self.font_size), text_color=FG_DIM)
        size_label.grid(row=1, column=2, padx=8, pady=4)

        preview = Text(
            win,
            height=4,
            bg=BG_DARK,
            fg=FG,
            font=(self.font_family, self.font_size),
            wrap="word",
            relief="flat",
        )
        preview.grid(row=2, column=0, columnspan=3, padx=12, pady=(8, 4), sticky="nsew")
        preview.insert("1.0", "The night is quiet.\nThis space is just for you.")
        preview.configure(state="disabled")

        def update_preview(*_: object) -> None:
            size_label.configure(text=str(size_var.get()))
            preview.configure(font=(font_var.get(), size_var.get()))

        size_slider.configure(command=lambda _: update_preview())
        font_var.trace_add("write", lambda *_: update_preview())
        update_preview()

        def apply_font() -> None:
            self.font_family = font_var.get()
            self.font_size = int(size_var.get())
            for t in self.tabs:
                t.text.configure(font=(self.font_family, self.font_size))
            win.destroy()

        apply_btn = ctk.CTkButton(
            win,
            text="Apply",
            fg_color=ACCENT,
            hover_color=ACCENT,
            text_color=BG,
            corner_radius=8,
            command=apply_font,
        )
        apply_btn.grid(row=3, column=0, columnspan=3, padx=12, pady=(4, 12), sticky="e")

        win.grid_columnconfigure(1, weight=1)
        win.grid_rowconfigure(2, weight=1)

    def _paste_handler(self, event=None):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is not None and hasattr(img, "size"):
                max_width = 600
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._images.append(photo)
                editor = event.widget if event else None
                if editor is None:
                    return None
                editor.image_create("insert", image=photo)
                editor.insert("insert", "\n")
                tab = self._get_current_tab()
                if tab:
                    self._mark_unsaved(tab)
                return "break"
        except Exception as e:
            print(f"Paste error: {e}")
        return None

    def insert_image(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return

        path = filedialog.askopenfilename(
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.gif *.webp"),
                ("All Files", "*.*"),
            ]
        )
        if not path:
            return

        img = Image.open(path)

        max_width = 600
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)

        photo = ImageTk.PhotoImage(img)
        self._images.append(photo)
        tab.text.image_create("insert", image=photo)
        tab.text.insert("insert", "\n")
        self._mark_unsaved(tab)

    def toggle_word_wrap(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return
        current = tab.text.cget("wrap")
        new_wrap = "none" if current == "word" else "word"
        tab.text.configure(wrap=new_wrap)

    def _ensure_ai_tags(self, text: Text) -> None:
        text.tag_configure("separator", foreground=ACCENT_D)
        text.tag_configure(
            "ai_label", foreground=ACCENT, font=("Consolas", 11, "bold")
        )
        text.tag_configure("user_msg", foreground=ACCENT)
        text.tag_configure("ai_reply", foreground=FG_EDITOR)

    def toggle_ai(self) -> None:
        if self._ai_mode:
            self._ai_turn_off()
        else:
            self._ai_turn_on()

    def _ai_turn_on(self) -> None:
        if self._ai_mode:
            return  # already on — never append a second separator
        tab = self._get_current_tab()
        if not tab:
            return
        self._ai_mode = True
        self.ai_toggle_btn.config(bg=ACCENT, fg=BG)

        text = tab.text
        current = text.get("1.0", "end-1c")
        if current.strip():
            prefix = "\n" if current.endswith("\n") else "\n\n"
            text.insert("end", prefix)

        # --- separator ---
        text.insert("end", _AI_SEP + "\n")
        idx = text.search(_AI_SEP, "end", backwards=True, stopindex="1.0")
        if idx:
            text.tag_add("separator", idx, f"{idx}+{len(_AI_SEP)}c")

        # --- "Noctis AI" label ---
        text.insert("end", "Noctis AI\n\n")
        idx2 = text.search("Noctis AI", "end", backwards=True, stopindex="1.0")
        if idx2:
            text.tag_add("ai_label", idx2, f"{idx2}+9c")

        # --- initial >>> prompt; user types here directly ---
        text.insert("end", ">>> ")
        idx3 = text.search(">>> ", "end", backwards=True, stopindex="1.0")
        if idx3:
            text.tag_add("user_msg", idx3, f"{idx3}+4c")

        text.see("end")
        text.mark_set("insert", "end")
        text.focus_set()

        self._ai_chat_history = []

    def _ai_turn_off(self) -> None:
        self._ai_mode = False
        self.ai_toggle_btn.config(bg="#1a2a1a", fg=FG_DIM)
        self._ai_chat_history = []

        tab = self._get_current_tab()
        if tab:
            tab.text.focus_set()

    def _handle_enter(self, event=None) -> Optional[str]:
        """Intercept Enter in the editor. If AI mode is on and cursor is on a
        >>> line with a message, dispatch to Ollama; otherwise let Enter pass."""
        if not self._ai_mode:
            return None

        tab = self._get_current_tab()
        if not tab:
            return None

        text = tab.text
        line = text.get("insert linestart", "insert lineend")

        if not line.startswith(">>> "):
            return None

        msg = line[4:].strip()
        if not msg:
            return "break"  # suppress Enter on blank >>> so the prompt line stays intact

        # Move cursor to end of the >>> line, then add thinking placeholder.
        # The leading \n\n creates the blank line that separates the prompt
        # from the AI reply once ">> thinking..." is cleared.
        text.mark_set("insert", "insert lineend")
        text.insert("insert", "\n\n>> thinking...")
        text.see("end")

        _msg = msg
        _thinking_cleared = [False]  # mutable flag shared across token callbacks
        messages_ctx = (
            [{"role": "system", "content": NOCTIS_SYSTEM_PROMPT}]
            + self._ai_chat_history
        )

        def on_token(token: str) -> None:
            def append() -> None:
                # Clear ">> thinking..." on the very first token
                if not _thinking_cleared[0]:
                    _thinking_cleared[0] = True
                    t_idx = text.search(
                        ">> thinking...", "end", backwards=True, stopindex="1.0"
                    )
                    if t_idx:
                        text.delete(t_idx, f"{t_idx}+14c")
                text.insert("end", token)
                text.see("end")
            self.after(0, append)

        def on_done(full_reply: str) -> None:
            def finish() -> None:
                text.insert("end", "\n\n>>> ")
                new_p = text.search(">>> ", "end", backwards=True, stopindex="1.0")
                if new_p:
                    text.tag_add("user_msg", new_p, f"{new_p}+4c")
                text.see("end")
                text.mark_set("insert", "end")
                if full_reply:
                    self._ai_chat_history.append(
                        {"role": "user", "content": _msg}
                    )
                    self._ai_chat_history.append(
                        {"role": "assistant", "content": full_reply}
                    )
            self.after(0, finish)

        def on_error() -> None:
            def show_err() -> None:
                t_idx = text.search(
                    ">> thinking...", "end", backwards=True, stopindex="1.0"
                )
                if t_idx:
                    text.delete(t_idx, f"{t_idx}+14c")
                text.insert("end", "Ollama is not running.\nRun: ollama serve")
                text.insert("end", "\n\n>>> ")
                new_p = text.search(">>> ", "end", backwards=True, stopindex="1.0")
                if new_p:
                    text.tag_add("user_msg", new_p, f"{new_p}+4c")
                text.see("end")
            self.after(0, show_err)

        stream_ollama(msg, messages_ctx, on_token, on_done, on_error)
        return "break"

    def _run_ai_request(
        self,
        system_prompt: str,
        user_text: str,
        on_success: Callable[[str], None],
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        def worker() -> None:
            try:
                prompt = f"{system_prompt}\n\n---\n\n{user_text.strip()}"
                response = requests.post(
                    AI_URL,
                    json={"model": AI_MODEL, "prompt": prompt, "stream": False},
                    timeout=300,
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "").strip()
                if not text:
                    raise ValueError("Empty response from model")
            except requests.RequestException:
                msg = "Start Ollama first: run 'ollama serve' in terminal"
                self.after(0, lambda: self._show_messagebox("Ollama Offline", msg))
                if on_error:
                    self.after(0, lambda: on_error(msg))
                return
            except Exception as exc:
                err = f"AI error: {exc}"
                if on_error:
                    self.after(0, lambda: on_error(err))
                return

            self.after(0, lambda: on_success(text))

        threading.Thread(target=worker, daemon=True).start()

    def ask_ai(self) -> None:
        if not self._ai_mode:
            self._ai_turn_on()
        else:
            tab = self._get_current_tab()
            if tab:
                tab.text.focus_set()

    def summarize_note(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return
        content = tab.text.get("1.0", "end-1c").strip()
        if not content:
            return

        loading_win = self._show_loading_popup("Summarizing...")

        def on_done(summary: str) -> None:
            loading_win.destroy()
            self._show_ai_response("Summary", summary)

        def on_error(_: str) -> None:
            loading_win.destroy()

        system_prompt = (
            "Summarize this note in a gentle, supportive way. "
            "Highlight key feelings and any small next steps."
        )
        self._run_ai_request(system_prompt, content, on_done, on_error)

    def fix_grammar(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return
        if not tab.text.tag_ranges("sel"):
            return
        selected = tab.text.get("sel.first", "sel.last").strip()
        if not selected:
            return

        loading_win = self._show_loading_popup("Fixing grammar...")

        def on_done(fixed: str) -> None:
            loading_win.destroy()
            tab.text.delete("sel.first", "sel.last")
            tab.text.insert("insert", fixed)
            self._mark_unsaved(tab)

        def on_error(_: str) -> None:
            loading_win.destroy()

        system_prompt = (
            "Improve the grammar and spelling of this text while keeping "
            "the original tone and meaning. Return only the corrected text."
        )
        self._run_ai_request(system_prompt, selected, on_done, on_error)

    def _show_ai_response(self, title: str, text: str) -> None:
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.configure(fg_color=BG_EDIT)
        win.geometry("600x420")

        textbox = Text(
            win,
            bg=BG_DARK,
            fg=FG,
            font=FONT,
            wrap="word",
            relief="flat",
            padx=12,
            pady=12,
        )
        textbox.pack(fill="both", expand=True, padx=12, pady=(12, 8))
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")

        def copy_text() -> None:
            self.clipboard_clear()
            self.clipboard_append(text)

        copy_btn = ctk.CTkButton(
            win,
            text="Copy",
            fg_color=ACCENT,
            hover_color=ACCENT,
            text_color=BG,
            corner_radius=8,
            command=copy_text,
        )
        copy_btn.pack(padx=12, pady=(0, 12), anchor="e")

    def _show_loading_popup(self, message: str) -> ctk.CTkToplevel:
        win = ctk.CTkToplevel(self)
        win.title("Please wait")
        win.configure(fg_color=BG_EDIT)
        win.resizable(False, False)

        ctk.CTkLabel(win, text=message, text_color=FG).pack(padx=16, pady=16)

        return win

    def _show_messagebox(self, title: str, message: str) -> None:
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.configure(fg_color=BG_EDIT)
        win.resizable(False, False)

        ctk.CTkLabel(
            win, text=message, text_color=FG, justify="left"
        ).pack(padx=16, pady=(16, 8))

        btn = ctk.CTkButton(
            win,
            text="OK",
            fg_color=ACCENT,
            hover_color=ACCENT,
            text_color=BG,
            corner_radius=8,
            command=win.destroy,
        )
        btn.pack(padx=16, pady=(0, 16))

    def _update_status_from_event(self, _event: object) -> None:
        self._update_status()

    def _update_status(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return
        text = tab.text
        index = text.index("insert")
        line, col = index.split(".")
        col_num = int(col) + 1
        content = text.get("1.0", "end-1c")
        words = len(content.split())
        status = f"Ln {line}  Col {col_num}  |  {words} words"
        self.status_label.configure(text=status)

    def _on_text_modified(self, event: object) -> None:
        widget = event.widget
        widget.edit_modified(False)

        for tab in self.tabs:
            if tab.text is widget:
                self._mark_unsaved(tab)
                break
        self._update_status()

    def _mark_unsaved(self, tab: TabInfo) -> None:
        if not tab.unsaved:
            tab.unsaved = True
            self._update_tab_title(tab)

    def _update_tab_title(self, tab: TabInfo) -> None:
        prefix = "● " if tab.unsaved else ""
        tab.button.config(text=self._truncate(prefix + tab.title))

    def _truncate(self, text: str, max_chars: int = 20) -> str:
        """Truncate a tab title to fit within the pill width."""
        if len(text) > max_chars:
            return text[: max_chars - 1] + "…"
        return text

    def _confirm_discard_changes(self, name: str) -> bool:
        msg = f"Discard unsaved changes in '{name}'?"
        result: Dict[str, bool] = {"answer": False}

        def set_answer(value: bool) -> None:
            result["answer"] = value
            dialog.destroy()

        dialog = ctk.CTkToplevel(self)
        dialog.title("Unsaved Changes")
        dialog.configure(fg_color=BG_EDIT)
        dialog.resizable(False, False)

        ctk.CTkLabel(
            dialog, text=msg, text_color=FG, justify="left"
        ).pack(padx=16, pady=(16, 8))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(padx=16, pady=(0, 16), anchor="e")

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color=BG_DARK,
            hover_color="#2d3d2d",
            text_color=FG,
            corner_radius=8,
            command=lambda: set_answer(False),
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame,
            text="Discard",
            fg_color=ACCENT,
            hover_color=ACCENT,
            text_color=BG,
            corner_radius=8,
            command=lambda: set_answer(True),
        ).pack(side="right", padx=4)

        dialog.grab_set()
        self.wait_window(dialog)
        return result["answer"]

    def show_about(self) -> None:
        message = (
            "Noctis v1.0\n"
            "Your private mental health space\n\n"
            "🔒 100% Local — No data ever leaves this machine\n"
            "Built with Python + CustomTkinter"
        )
        self._show_messagebox("Noctis", message)

    def _create_keybindings(self) -> None:
        self.bind("<Control-n>", lambda _e: self.new_tab())
        self.bind("<Control-N>", lambda _e: self.new_tab())
        self.bind("<Control-o>", lambda _e: self.open_file())
        self.bind("<Control-O>", lambda _e: self.open_file())
        self.bind("<Control-s>", lambda _e: self.save_file())
        self.bind("<Control-S>", lambda _e: self.save_file())
        self.bind("<Control-Shift-S>", lambda _e: self.save_file_as())
        self.bind("<Control-w>", lambda _e: self.close_tab())
        self.bind("<Control-W>", lambda _e: self.close_tab())
        self.bind("<Control-z>", lambda _e: self._editor_undo())
        self.bind("<Control-Z>", lambda _e: self._editor_undo())
        self.bind("<Control-y>", lambda _e: self._editor_redo())
        self.bind("<Control-Y>", lambda _e: self._editor_redo())
        self.bind("<Control-f>", lambda _e: self.open_find_replace())
        self.bind("<Control-F>", lambda _e: self.open_find_replace())
        self.bind("<Control-a>", lambda _e: self._editor_select_all())
        self.bind("<Control-A>", lambda _e: self._editor_select_all())
        self.bind("<Control-Shift-I>", lambda _e: self.insert_image())

        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def on_exit(self) -> None:
        for tab in list(self.tabs):
            if tab.unsaved:
                if not self._confirm_discard_changes(tab.title):
                    return
        self.destroy()
