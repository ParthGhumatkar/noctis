from __future__ import annotations

import ctypes
import json
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import (
    Button, Entry, Frame, Label, OptionMenu,
    Scrollbar, Spinbox, StringVar, IntVar,
    Text, Toplevel, colorchooser, filedialog,
)
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageTk
from typing import Callable, Dict, List, Optional

import requests

# ── 2024 Modern Deep-Dark Color Palette ──────────────────────────────────────
BG_WINDOW    = "#0d1117"   # deepest — window, editor, tab bar
BG_SURFACE   = "#161b22"   # raised — menu bar, dialog backgrounds
BG_ELEVATED  = "#1c2128"   # interactive hover / active elements

FG_PRIMARY   = "#e6edf3"
FG_SECONDARY = "#7d8590"
FG_TERTIARY  = "#484f58"

ACCENT       = "#7ab648"
ACCENT_HOVER = "#8fd74f"
ACCENT_DARK  = "#238636"
ACCENT_SUBTLE= "#2ea043"

BORDER       = "#30363d"
DIVIDER      = "#21262d"
SELECT_BG    = "#1f3244"
CURSOR_CLR   = "#7ab648"
CLOSE_RED    = "#f85149"

# ── Custom menu-specific tokens ───────────────────────────────────────────────
DROPDOWN_BG     = "#1c2128"   # dropdown panel background
MENU_ITEM_HOVER = "#243b24"   # item hover — deep green tint (readable, branded)

# ── Backward-compat aliases ───────────────────────────────────────────────────
WIN_BG    = BG_WINDOW
MENU_BG   = BG_SURFACE
EDITOR_BG = BG_WINDOW
EDITOR_FG = FG_PRIMARY
FG        = FG_PRIMARY
FG_DIM    = FG_SECONDARY
HOVER_BG  = BG_ELEVATED
ACCENT_AI = ACCENT
BG_DARK   = "#0a0e14"
ACCENT_D  = "#1a2f1a"

# ── Theme Presets ─────────────────────────────────────────────────────────────
# Each theme fully specifies the palette consumed by apply_theme().
THEMES: Dict[str, Dict[str, str]] = {
    "Dark (Default)": {
        "BG_WINDOW": "#0d1117", "BG_SURFACE": "#161b22", "BG_ELEVATED": "#1c2128",
        "FG_PRIMARY": "#e6edf3", "FG_SECONDARY": "#7d8590", "FG_TERTIARY": "#484f58",
        "ACCENT": "#7ab648", "ACCENT_HOVER": "#8fd74f",
        "ACCENT_DARK": "#238636", "ACCENT_SUBTLE": "#2ea043",
        "BORDER": "#30363d", "DIVIDER": "#21262d",
        "SELECT_BG": "#1f3244", "CURSOR_CLR": "#7ab648",
        "DROPDOWN_BG": "#1c2128", "MENU_ITEM_HOVER": "#243b24",
    },
    "Light": {
        "BG_WINDOW": "#ffffff", "BG_SURFACE": "#f6f8fa", "BG_ELEVATED": "#eaeef2",
        "FG_PRIMARY": "#1f2328", "FG_SECONDARY": "#57606a", "FG_TERTIARY": "#8c959f",
        "ACCENT": "#2ea043", "ACCENT_HOVER": "#3fb950",
        "ACCENT_DARK": "#1a7f37", "ACCENT_SUBTLE": "#2ea043",
        "BORDER": "#d0d7de", "DIVIDER": "#d8dee4",
        "SELECT_BG": "#ddf4ff", "CURSOR_CLR": "#2ea043",
        "DROPDOWN_BG": "#f6f8fa", "MENU_ITEM_HOVER": "#ddf4e8",
    },
    "Gruvbox Dark": {
        "BG_WINDOW": "#282828", "BG_SURFACE": "#32302f", "BG_ELEVATED": "#3c3836",
        "FG_PRIMARY": "#ebdbb2", "FG_SECONDARY": "#a89984", "FG_TERTIARY": "#928374",
        "ACCENT": "#b8bb26", "ACCENT_HOVER": "#c8cc3a",
        "ACCENT_DARK": "#98971a", "ACCENT_SUBTLE": "#79740e",
        "BORDER": "#504945", "DIVIDER": "#3c3836",
        "SELECT_BG": "#45403d", "CURSOR_CLR": "#b8bb26",
        "DROPDOWN_BG": "#3c3836", "MENU_ITEM_HOVER": "#504945",
    },
    "Nord": {
        "BG_WINDOW": "#2e3440", "BG_SURFACE": "#3b4252", "BG_ELEVATED": "#434c5e",
        "FG_PRIMARY": "#eceff4", "FG_SECONDARY": "#d8dee9", "FG_TERTIARY": "#4c566a",
        "ACCENT": "#88c0d0", "ACCENT_HOVER": "#9dcfe0",
        "ACCENT_DARK": "#5e81ac", "ACCENT_SUBTLE": "#81a1c1",
        "BORDER": "#4c566a", "DIVIDER": "#3b4252",
        "SELECT_BG": "#3b4252", "CURSOR_CLR": "#88c0d0",
        "DROPDOWN_BG": "#434c5e", "MENU_ITEM_HOVER": "#4c566a",
    },
    "Dracula": {
        "BG_WINDOW": "#282a36", "BG_SURFACE": "#21222c", "BG_ELEVATED": "#44475a",
        "FG_PRIMARY": "#f8f8f2", "FG_SECONDARY": "#6272a4", "FG_TERTIARY": "#44475a",
        "ACCENT": "#50fa7b", "ACCENT_HOVER": "#69ff94",
        "ACCENT_DARK": "#00b452", "ACCENT_SUBTLE": "#50fa7b",
        "BORDER": "#44475a", "DIVIDER": "#373844",
        "SELECT_BG": "#44475a", "CURSOR_CLR": "#50fa7b",
        "DROPDOWN_BG": "#44475a", "MENU_ITEM_HOVER": "#2d3047",
    },
    "Monokai": {
        "BG_WINDOW": "#272822", "BG_SURFACE": "#1e1f1c", "BG_ELEVATED": "#3e3d32",
        "FG_PRIMARY": "#f8f8f2", "FG_SECONDARY": "#75715e", "FG_TERTIARY": "#49483e",
        "ACCENT": "#a6e22e", "ACCENT_HOVER": "#b6f240",
        "ACCENT_DARK": "#86c520", "ACCENT_SUBTLE": "#a6e22e",
        "BORDER": "#49483e", "DIVIDER": "#3e3d32",
        "SELECT_BG": "#49483e", "CURSOR_CLR": "#a6e22e",
        "DROPDOWN_BG": "#3e3d32", "MENU_ITEM_HOVER": "#3a3a2f",
    },
    "Solarized Dark": {
        "BG_WINDOW": "#002b36", "BG_SURFACE": "#073642", "BG_ELEVATED": "#094552",
        "FG_PRIMARY": "#839496", "FG_SECONDARY": "#657b83", "FG_TERTIARY": "#586e75",
        "ACCENT": "#859900", "ACCENT_HOVER": "#9aad00",
        "ACCENT_DARK": "#6c7d00", "ACCENT_SUBTLE": "#859900",
        "BORDER": "#073642", "DIVIDER": "#073642",
        "SELECT_BG": "#073642", "CURSOR_CLR": "#859900",
        "DROPDOWN_BG": "#094552", "MENU_ITEM_HOVER": "#0d5060",
    },
    "GitHub Dark": {
        "BG_WINDOW": "#0d1117", "BG_SURFACE": "#161b22", "BG_ELEVATED": "#1c2128",
        "FG_PRIMARY": "#e6edf3", "FG_SECONDARY": "#7d8590", "FG_TERTIARY": "#484f58",
        "ACCENT": "#238636", "ACCENT_HOVER": "#2ea043",
        "ACCENT_DARK": "#1a7f37", "ACCENT_SUBTLE": "#196c2e",
        "BORDER": "#30363d", "DIVIDER": "#21262d",
        "SELECT_BG": "#1f3244", "CURSOR_CLR": "#238636",
        "DROPDOWN_BG": "#1c2128", "MENU_ITEM_HOVER": "#1a2f1a",
    },
}

# ── Theme validation helpers ──────────────────────────────────────────────────

def _contrast_ratio(hex1: str, hex2: str) -> float:
    """Return the WCAG relative-luminance contrast ratio for two hex colours.
    A ratio of 1 means identical; higher is better. Returns 0 on bad input."""
    def _lum(h: str) -> float:
        h = h.lstrip("#")
        if len(h) != 6:
            raise ValueError
        r, g, b = (int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        def _lin(v: float) -> float:
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)
    try:
        L1, L2 = _lum(hex1), _lum(hex2)
        hi, lo  = max(L1, L2), min(L1, L2)
        return (hi + 0.05) / (lo + 0.05)
    except Exception:
        return 0.0


def validate_theme(t: Dict[str, str]) -> tuple:
    """Return (ok: bool, message: str) after checking the theme for usability.

    Checked against our actual key names (BG_WINDOW, FG_PRIMARY, ACCENT,
    BG_ELEVATED).  All preset themes pass these rules by construction.
    """
    bw = t.get("BG_WINDOW", "")
    fp = t.get("FG_PRIMARY", "")
    ac = t.get("ACCENT",     "")
    be = t.get("BG_ELEVATED","")

    # Rule 1 — text vs background must be readable (WCAG AA minimum = 4.5:1)
    cr = _contrast_ratio(bw, fp)
    if cr < 4.5:
        return (False,
                f"Text vs background contrast is {cr:.1f}:1 — "
                "need at least 4.5:1 (WCAG AA). "
                "Try a lighter text colour or a darker background.")

    # Rule 2 — accent must differ from the background
    if bw.strip().lower() == ac.strip().lower():
        return False, "Accent colour cannot be identical to the background colour."

    # Rule 3 — text must differ from background
    if bw.strip().lower() == fp.strip().lower():
        return False, "Primary text colour cannot match the background colour."

    # Rule 4 — need at least 3 distinct colours in the core palette
    unique = len({bw.lower(), fp.lower(), ac.lower(), be.lower()})
    if unique < 3:
        return False, "Theme must use at least 3 distinct colours."

    return True, ""


# ── AI / Ollama ───────────────────────────────────────────────────────────────
AI_URL      = "http://localhost:11434/api/generate"
AI_CHAT_URL = "http://localhost:11434/api/chat"
AI_MODEL    = "noctis-ai-v1"

NOCTIS_SYSTEM_PROMPT = (
    "You are Noctis, a warm and private AI companion running 100% locally on this "
    "device. No internet. No data leaves this machine. You are embedded in a private "
    "mental health notepad. Be calm, warm, concise and non-judgmental. Never mention "
    "being a cloud service or having internet access. You are fully local and private."
)

_AI_SEP = "─────────────────────────────"


# ── Pure-logic helpers ────────────────────────────────────────────────────────

def stream_ollama(
    prompt: str,
    history: List[Dict[str, str]],
    on_token: Callable[[str], None],
    on_done: Callable[[str], None],
    on_error: Callable[[], None],
) -> None:
    def run() -> None:
        try:
            messages   = history + [{"role": "user", "content": prompt}]
            full_reply = ""
            with requests.post(
                AI_CHAT_URL,
                json={"model": AI_MODEL, "messages": messages, "stream": True},
                stream=True,
                timeout=300,
            ) as r:
                for raw in r.iter_lines():
                    if not raw:
                        continue
                    chunk = json.loads(raw)
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
    frame:        Frame
    button:       tk.Widget        # title Label (text/color compat alias)
    close_button: Button
    indicator:    Frame
    text:         Text
    file_path:    Optional[Path]
    title:        str
    unsaved:      bool  = False
    # premium tab layout extras (all set during new_tab)
    tab_outer:    Optional[Frame]     = None  # outermost container in tabs_container
    tab_inner:    Optional[Frame]     = None  # inner row (icon + title + dot + close)
    icon_label:   Optional[Label]     = None  # 📄 saved / 📝 unsaved
    dot_label:    Optional[Label]     = None  # ● green unsaved dot
    scrollbar:    Optional[Scrollbar] = None  # editor scrollbar (for re-theming)


def dark_titlebar(window) -> None:
    window.update()
    set_attr = ctypes.windll.dwmapi.DwmSetWindowAttribute
    hwnd     = ctypes.windll.user32.GetParent(window.winfo_id())
    val      = ctypes.c_int(1)
    set_attr(hwnd, 20, ctypes.byref(val), ctypes.sizeof(val))


# ── Widget factory helpers ────────────────────────────────────────────────────

def _make_btn(
    parent,
    text: str,
    command,
    primary: bool = False,
    danger:  bool = False,
    **kw,
) -> Button:
    if primary:
        bg, fg, abg = ACCENT_DARK, "#ffffff", ACCENT_SUBTLE
    elif danger:
        bg, fg, abg = "#c42b1c", "#ffffff", "#a82315"
    else:
        bg, fg, abg = BG_ELEVATED, FG_PRIMARY, "#252c36"
    return Button(
        parent,
        text=text, command=command,
        bg=bg, fg=fg,
        activebackground=abg, activeforeground=fg,
        relief="flat", cursor="hand2",
        padx=14, pady=7, bd=0,
        font=("Segoe UI", 9),
        **kw,
    )


def _make_entry(parent, width: int = 30, **kw) -> Entry:
    return Entry(
        parent,
        width=width,
        bg=BG_ELEVATED, fg=FG_PRIMARY,
        insertbackground=FG_PRIMARY,
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT,
        font=("Segoe UI", 9),
        **kw,
    )


def _make_dialog(
    parent,
    title:     str,
    width:     int  = 420,
    height:    int  = 220,
    resizable: bool = False,
) -> Toplevel:
    win = Toplevel(parent)
    win.title(title)
    win.configure(bg=BG_SURFACE)
    win.resizable(resizable, resizable)
    px = parent.winfo_x() + (parent.winfo_width()  - width)  // 2
    py = parent.winfo_y() + (parent.winfo_height() - height) // 2
    win.geometry(f"{width}x{height}+{px}+{py}")
    try:
        dark_titlebar(win)
    except Exception:
        pass
    return win


# ── Modern Dropdown ───────────────────────────────────────────────────────────

class ModernDropdown(Toplevel):
    """Borderless, always-on-top dropdown menu panel.

    Accepts a list of item dicts:
      {"type": "command", "icon": str, "label": str,
       "shortcut": str, "command": callable}
      {"type": "separator"}
      {"type": "header", "label": str}
    """

    WIDTH  = 268
    ITEM_H = 36
    SEP_H  = 9    # 1 px line + 4 px padding each side

    def __init__(
        self,
        parent:   tk.Misc,
        items:    List[Dict],
        x:        int,
        y:        int,
        on_close: Optional[Callable] = None,
    ) -> None:
        super().__init__(parent)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg=BORDER)          # 1 px border via outer bg

        self._on_close   = on_close
        self._cmd_items: List[tuple] = []  # (frame, [widgets], item_dict)
        self._nav_idx    = -1

        # ── height calculation ────────────────────────────────────────────────
        total_h = 2  # top + bottom border
        for it in items:
            total_h += self.SEP_H if it.get("type") == "separator" else self.ITEM_H

        # ── guard against screen edges ────────────────────────────────────────
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        gx = min(x, sw - self.WIDTH  - 4)
        gy = min(y, sh - total_h - 4)

        self.geometry(f"{self.WIDTH}x{total_h}+{gx}+{gy}")

        # ── inner panel (inset 1 px for border) ───────────────────────────────
        inner = Frame(self, bg=DROPDOWN_BG)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        self._build_items(inner, items)

        # ── Windows DWM drop-shadow ───────────────────────────────────────────
        try:
            self.update()
            hwnd  = ctypes.windll.user32.GetParent(self.winfo_id())
            style = ctypes.windll.user32.GetClassLongW(hwnd, -26)
            ctypes.windll.user32.SetClassLongW(hwnd, -26, style | 0x00020000)
        except Exception:
            pass

        self.bind("<Escape>",  lambda _e: self.close())
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Down>",    self._nav_down)
        self.bind("<Up>",      self._nav_up)
        self.bind("<Return>",  self._activate_nav)

        self.focus_set()

    # ── item building ─────────────────────────────────────────────────────────

    def _build_items(self, parent: Frame, items: List[Dict]) -> None:
        cmd_idx = 0
        for item in items:
            t = item.get("type", "command")
            if t == "separator":
                Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=8, pady=4)
            elif t == "header":
                Label(
                    parent,
                    text=item.get("label", "").upper(),
                    bg=DROPDOWN_BG, fg=FG_TERTIARY,
                    font=("Segoe UI", 8, "bold"),
                    anchor="w",
                ).pack(fill="x", padx=16, pady=(8, 2))
            else:
                self._build_command(parent, item, cmd_idx)
                cmd_idx += 1

    def _build_command(self, parent: Frame, item: Dict, nav_i: int) -> None:
        row = Frame(parent, bg=DROPDOWN_BG, height=self.ITEM_H, cursor="hand2")
        row.pack(fill="x")
        row.pack_propagate(False)

        icon_lbl = Label(
            row,
            text=item.get("icon", "  "),
            bg=DROPDOWN_BG, fg=FG_PRIMARY,
            font=("Segoe UI", 10),
            width=3, anchor="center",
        )
        icon_lbl.pack(side="left", padx=(6, 0))

        text_lbl = Label(
            row,
            text=item.get("label", ""),
            bg=DROPDOWN_BG, fg=FG_PRIMARY,
            font=("Segoe UI", 10),
            anchor="w",
        )
        text_lbl.pack(side="left", fill="x", expand=True, padx=(6, 0))

        sc: Optional[Label] = None
        if item.get("shortcut"):
            sc = Label(
                row,
                text=item["shortcut"],
                bg=DROPDOWN_BG, fg=FG_SECONDARY,
                font=("Segoe UI", 8),
                anchor="e",
            )
            sc.pack(side="right", padx=(0, 14))

        all_w = [row, icon_lbl, text_lbl] + ([sc] if sc else [])
        self._cmd_items.append((row, all_w, item))

        # ── hover ─────────────────────────────────────────────────────────────
        def _enter(_e, ws=all_w):
            for w in ws:
                w.config(bg=MENU_ITEM_HOVER)

        def _leave(_e, ws=all_w, i=nav_i):
            bg = MENU_ITEM_HOVER if i == self._nav_idx else DROPDOWN_BG
            for w in ws:
                w.config(bg=bg)

        # ── click ─────────────────────────────────────────────────────────────
        def _click(_e=None, cmd=item.get("command")):
            self.close()
            if cmd:
                cmd()

        for w in all_w:
            w.bind("<Enter>",    _enter)
            w.bind("<Leave>",    _leave)
            w.bind("<Button-1>", _click)

    # ── keyboard navigation ───────────────────────────────────────────────────

    def _set_nav(self, idx: int) -> None:
        for i, (_, ws, _) in enumerate(self._cmd_items):
            bg = MENU_ITEM_HOVER if i == idx else DROPDOWN_BG
            for w in ws:
                try:
                    w.config(bg=bg)
                except Exception:
                    pass
        self._nav_idx = idx

    def _nav_down(self, _e) -> None:
        if self._cmd_items:
            self._set_nav((self._nav_idx + 1) % len(self._cmd_items))

    def _nav_up(self, _e) -> None:
        if self._cmd_items:
            self._set_nav((self._nav_idx - 1) % len(self._cmd_items))

    def _activate_nav(self, _e) -> None:
        if 0 <= self._nav_idx < len(self._cmd_items):
            _, _, item = self._cmd_items[self._nav_idx]
            cmd = item.get("command")
            self.close()
            if cmd:
                cmd()

    # ── focus-loss auto-close ─────────────────────────────────────────────────

    def _on_focus_out(self, _e) -> None:
        self.after(90, self._maybe_close)

    def _maybe_close(self) -> None:
        try:
            if not self.winfo_exists():
                return
            fw = self.focus_get()
            if fw is None or not str(fw).startswith(str(self)):
                self.close()
        except Exception:
            pass

    # ── public close ─────────────────────────────────────────────────────────

    def close(self) -> None:
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        if self._on_close:
            cb, self._on_close = self._on_close, None
            cb()
        try:
            self.destroy()
        except Exception:
            pass


# ── First-launch Setup Wizard ─────────────────────────────────────────────────

class SetupWizard(Toplevel):
    """One-time GUI wizard that pulls llama3.2:3b and creates noctis-ai-v1.

    Uses the Ollama HTTP API for real-time MB/s progress during the download
    and subprocess for model creation.  Always stays on top; the close button
    is disabled while a setup step is actively running.

    Call ``SetupWizard.is_needed()`` before creating an instance.
    """

    _BASE_MODEL   = "llama3.2:3b"
    _CUSTOM_MODEL = "noctis-ai-v1"
    _MODELFILE    = "NoctisModel.v1"
    _OLLAMA_API   = "http://localhost:11434"

    # ── construction ────────────────────────────────────────────────────────

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("Noctis — First Time Setup  (DO NOT CLOSE)")
        self.configure(bg=BG_WINDOW)
        self.resizable(False, False)
        self.wm_attributes("-topmost", True)          # always on top

        self._active = False                           # True while steps run
        self.protocol("WM_DELETE_WINDOW", self._guard_close)

        try:
            dark_titlebar(self)
        except Exception:
            pass

        self._build_ui()

        # Center on screen
        self.update_idletasks()
        w, h = 640, 510
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")

        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()

        self.after(350, self._begin)

    def _build_ui(self) -> None:
        # ── Top accent bar ────────────────────────────────────────────────
        Frame(self, bg=ACCENT, height=3).pack(fill="x")

        # ── Header ───────────────────────────────────────────────────────
        hdr = Frame(self, bg=BG_SURFACE)
        hdr.pack(fill="x")
        Label(hdr, text="🌙  Noctis  —  First Time Setup",
              bg=BG_SURFACE, fg=FG_PRIMARY,
              font=("Segoe UI", 14, "bold")).pack(pady=(12, 2))
        Label(hdr, text="Downloading your private AI companion  —  one time only (~2 GB)",
              bg=BG_SURFACE, fg=FG_SECONDARY,
              font=("Segoe UI", 9)).pack(pady=(0, 10))
        Frame(hdr, bg=BORDER, height=1).pack(fill="x")

        # ── Step indicators ───────────────────────────────────────────────
        steps_frm = Frame(self, bg=BG_WINDOW)
        steps_frm.pack(fill="x", padx=24, pady=(10, 4))
        self._step_lbls: List[Label] = []
        for txt in [
            "①  Download base model  (llama3.2:3b  ≈ 2 GB)",
            "②  Build Noctis AI companion  (noctis-ai-v1)",
            "③  Ready",
        ]:
            lbl = Label(steps_frm, text=txt, bg=BG_WINDOW, fg=FG_TERTIARY,
                        font=("Segoe UI", 9), anchor="w")
            lbl.pack(fill="x", pady=1)
            self._step_lbls.append(lbl)

        # ── Progress area ─────────────────────────────────────────────────
        Frame(self, bg=DIVIDER, height=1).pack(fill="x", pady=(6, 0))
        prog_frm = Frame(self, bg=BG_WINDOW)
        prog_frm.pack(fill="x", padx=24, pady=(8, 2))

        self._status_lbl = Label(prog_frm, text="Initialising…",
                                 bg=BG_WINDOW, fg=ACCENT,
                                 font=("Segoe UI", 10, "bold"), anchor="w")
        self._status_lbl.pack(fill="x")

        # taller progress bar for visibility
        self._track = Frame(prog_frm, bg=BG_ELEVATED, height=14)
        self._track.pack(fill="x", pady=(6, 2))
        self._track.pack_propagate(False)
        self._bar = Frame(self._track, bg=ACCENT, height=14, width=0)
        self._bar.place(x=0, y=0, relheight=1.0, width=0)

        # detail row: left = MB info,  right = percent
        det_row = Frame(prog_frm, bg=BG_WINDOW)
        det_row.pack(fill="x")
        self._detail_lbl = Label(det_row, text="",
                                 bg=BG_WINDOW, fg=FG_SECONDARY,
                                 font=("Segoe UI", 8), anchor="w")
        self._detail_lbl.pack(side="left")
        self._pct_lbl = Label(det_row, text="",
                              bg=BG_WINDOW, fg=FG_TERTIARY,
                              font=("Segoe UI", 8))
        self._pct_lbl.pack(side="right")

        # ── Scrollable log ────────────────────────────────────────────────
        Frame(self, bg=DIVIDER, height=1).pack(fill="x", pady=(6, 0))
        log_outer = Frame(self, bg=BG_WINDOW)
        log_outer.pack(fill="both", expand=True)

        log_sb = Scrollbar(log_outer, orient="vertical",
                           bg=BG_WINDOW, troughcolor=BG_WINDOW,
                           activebackground=BORDER, relief="flat",
                           width=6, bd=0, highlightthickness=0)
        self._log = Text(log_outer, bg=BG_WINDOW, fg=FG_TERTIARY,
                         font=("Consolas", 8), relief="flat", bd=0,
                         padx=12, pady=8, state="disabled",
                         wrap="char", highlightthickness=0,
                         yscrollcommand=log_sb.set)
        log_sb.config(command=self._log.yview)
        log_sb.pack(side="right", fill="y")
        self._log.pack(fill="both", expand=True)

        # ── Button row ────────────────────────────────────────────────────
        Frame(self, bg=BORDER, height=1).pack(fill="x")
        btn_frm = Frame(self, bg=BG_SURFACE)
        btn_frm.pack(fill="x")

        self._skip_btn = _make_btn(btn_frm, "Skip Setup", self._guard_close)
        self._skip_btn.pack(side="left", padx=14, pady=10)

        self._action_btn = _make_btn(btn_frm, "Continue  →", self._close,
                                     primary=True)
        self._action_btn.config(state="disabled")
        self._action_btn.pack(side="right", padx=14, pady=10)

    # ── thread-safe UI helpers ───────────────────────────────────────────────

    def _ui(self, fn) -> None:
        try:
            self.after(0, fn)
        except Exception:
            pass

    def _set_status(self, msg: str, colour: str = ACCENT) -> None:
        self._ui(lambda: self._status_lbl.config(text=msg, fg=colour))

    def _set_detail(self, msg: str) -> None:
        self._ui(lambda: self._detail_lbl.config(text=msg))

    def _set_pct(self, pct: float) -> None:
        def _do():
            try:
                w = int(self._track.winfo_width() * max(0.0, min(pct, 100.0)) / 100)
                self._bar.place(x=0, y=0, relheight=1.0, width=w)
                self._pct_lbl.config(text=f"{int(pct)} %")
            except Exception:
                pass
        self._ui(_do)

    def _light_step(self, idx: int) -> None:
        def _do():
            for i, lbl in enumerate(self._step_lbls):
                if i < idx:
                    lbl.config(fg=ACCENT, font=("Segoe UI", 9))
                elif i == idx:
                    lbl.config(fg=FG_PRIMARY, font=("Segoe UI", 9, "bold"))
                else:
                    lbl.config(fg=FG_TERTIARY, font=("Segoe UI", 9))
        self._ui(_do)

    def _log_line(self, text: str) -> None:
        def _do():
            self._log.config(state="normal")
            self._log.insert("end", text + "\n")
            self._log.see("end")
            self._log.config(state="disabled")
        self._ui(_do)

    def _guard_close(self) -> None:
        """Allow close only when no step is actively running."""
        if not self._active:
            self._close()

    # ── setup orchestration ──────────────────────────────────────────────────

    def _begin(self) -> None:
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        self._active = True
        try:
            self._log_line("=" * 56)
            self._log_line("  NOCTIS AI MODEL SETUP")
            self._log_line("=" * 56)

            # 0 — check Ollama
            self._set_status("Checking Ollama…")
            self._log_line("")
            if not self._check_ollama():
                return

            # 1 — pull base model via HTTP API (real MB progress)
            self._light_step(0)
            self._log_line("")
            self._log_line("STEP 1 — Downloading llama3.2:3b  (≈ 2 GB)")
            self._log_line(f"  POST {self._OLLAMA_API}/api/pull")
            if not self._pull_base():
                return

            # 2 — create custom model
            self._light_step(1)
            self._log_line("")
            self._log_line("STEP 2 — Building noctis-ai-v1")
            if not self._create_custom():
                return

            # 3 — success
            self._light_step(2)
            self._set_pct(100)
            self._set_status("✓  Setup complete — Noctis AI is ready!", ACCENT)
            self._set_detail("Model: noctis-ai-v1  •  100%  •  All done!")
            self._log_line("")
            self._log_line("=" * 56)
            self._log_line("  SETUP COMPLETE  ✓")
            self._log_line("=" * 56)
            self._log_line("  Closing automatically in 3 seconds…")
            self._mark_done()
            self._ui(lambda: (
                self._action_btn.config(state="normal"),
                self._skip_btn.config(state="disabled"),
            ))
            self._ui(lambda: self.after(3000, self._close))
        finally:
            self._active = False

    # ── individual steps ─────────────────────────────────────────────────────

    def _check_ollama(self) -> bool:
        try:
            r = requests.get(f"{self._OLLAMA_API}/api/tags", timeout=8)
            if r.status_code == 200:
                self._log_line("  Ollama service: OK")
                return True
        except Exception:
            pass

        # Fall back to subprocess check
        try:
            r2 = subprocess.run(["ollama", "list"],
                                capture_output=True, text=True, timeout=10)
            if r2.returncode == 0:
                self._log_line("  Ollama CLI: OK")
                return True
        except FileNotFoundError:
            pass
        except Exception as exc:
            self._log_line(f"  subprocess error: {exc}")

        self._set_status("⚠  Ollama not found or not running.", "#f85149")
        self._log_line(
            "\n  Ollama is not installed or not running.\n"
            "  → Download: https://ollama.com/download\n"
            "  → Start it, then click Re-run Setup from Help menu.\n"
            "\n  Click 'Skip Setup' to use Noctis without AI for now."
        )
        self._ui(lambda: self._skip_btn.config(state="normal"))
        return False

    def _pull_base(self) -> bool:
        """Pull llama3.2:3b via the Ollama HTTP API — streams real MB progress."""
        self._set_status(f"⬇  Downloading {self._BASE_MODEL} …")
        self._set_detail("Connecting to Ollama…")
        try:
            resp = requests.post(
                f"{self._OLLAMA_API}/api/pull",
                json={"name": self._BASE_MODEL},
                stream=True,
                timeout=3600,
            )
            resp.raise_for_status()

            total     = 0
            completed = 0
            last_log  = -10  # log threshold (% milestone)

            for raw in resp.iter_lines():
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except ValueError:
                    continue

                status = data.get("status", "")

                # First packet that carries size information
                if data.get("total") and total == 0:
                    total = data["total"]
                    mb_total = total / 1_048_576
                    self._log_line(f"  Total size: {mb_total:.1f} MB")

                if data.get("completed") and total > 0:
                    completed = data["completed"]
                    pct       = completed / total * 100
                    mb_done   = completed / 1_048_576
                    mb_total  = total     / 1_048_576

                    self._set_pct(pct * 0.80)        # 0 → 80 % of bar
                    self._set_status(
                        f"⬇  Downloading {self._BASE_MODEL} …  {pct:.0f} %"
                    )
                    self._set_detail(
                        f"{mb_done:.1f} MB / {mb_total:.1f} MB  ({pct:.0f} %)"
                    )
                    if pct >= last_log + 10:
                        self._log_line(
                            f"  {pct:.0f}%   {mb_done:.1f} / {mb_total:.1f} MB"
                        )
                        last_log = int(pct // 10) * 10
                elif status:
                    self._log_line(f"  {status}")
                    self._set_detail(status)

                if status == "success" or data.get("done"):
                    break

            self._log_line("  ✓ Download complete.")
            self._set_pct(80)
            return True

        except Exception as exc:
            self._log_line(f"\n  ✗ Download error: {exc}")
            self._set_status(f"⚠  Download failed — {exc}", "#f85149")
            self._set_detail("")
            self._ui(lambda: self._skip_btn.config(state="normal"))
            return False

    def _create_custom(self) -> bool:
        """Build noctis-ai-v1 via subprocess (ollama create)."""
        meipass    = Path(getattr(sys, "_MEIPASS", ""))
        script_dir = Path(__file__).resolve().parent
        modelfile  = next(
            (p for p in (meipass / self._MODELFILE, script_dir / self._MODELFILE)
             if p.exists()),
            None,
        )
        if modelfile is None:
            self._log_line(f"  ⚠  {self._MODELFILE} not found — skipping.")
            self._set_pct(99)
            return True  # non-fatal; base model still works

        cmd = ["ollama", "create", self._CUSTOM_MODEL, "-f", str(modelfile)]
        self._log_line(f"  $ {' '.join(cmd)}")
        self._set_status(f"🔨  Building {self._CUSTOM_MODEL} …")
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            steps = 0
            for raw in proc.stdout:
                line = raw.rstrip()
                if not line:
                    continue
                self._log_line(f"  {line}")
                self._set_detail(line[:72])
                steps += 1
                self._set_pct(80 + min(steps * 2, 18))  # 80 → 98 %
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"exit code {proc.returncode}")
            self._log_line("  ✓ Model created.")
            return True
        except Exception as exc:
            self._log_line(f"\n  ✗ Create error: {exc}")
            self._set_status(f"⚠  Model creation failed — {exc}", "#f85149")
            self._show_retry()
            return False

    # ── helpers ──────────────────────────────────────────────────────────────

    def _show_retry(self) -> None:
        def _do():
            self._skip_btn.config(state="normal")
            retry = _make_btn(
                self._action_btn.master,
                "Retry",
                self._retry,
            )
            retry.pack(side="right", padx=(0, 8), pady=10,
                       before=self._action_btn)
        self._ui(_do)

    def _retry(self) -> None:
        self._close()
        # Re-open: the parent Noctis.__init__ already wait_window-ed; we
        # must schedule a fresh wizard on the parent widget.
        try:
            parent = self.master
            parent.after(100, lambda: (
                parent.withdraw(),
                SetupWizard(parent),
            ))
        except Exception:
            pass

    @staticmethod
    def _config_path() -> Path:
        return Path.home() / ".noctis" / "config.json"

    def _mark_done(self) -> None:
        p = self._config_path()
        try:
            p.parent.mkdir(exist_ok=True)
            cfg: Dict[str, object] = {}
            if p.exists():
                cfg = json.loads(p.read_text(encoding="utf-8"))
            cfg["setup_done"] = True
            p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _close(self) -> None:
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass

    def _skip(self) -> None:
        """Skip without marking done — wizard shows again next launch."""
        self._close()

    # ── public API ──────────────────────────────────────────────────────────

    @staticmethod
    def is_needed() -> bool:
        """Return True if the first-time setup has not been completed yet."""
        p = Path.home() / ".noctis" / "config.json"
        if not p.exists():
            return True
        try:
            return not json.loads(p.read_text(encoding="utf-8")).get(
                "setup_done", False
            )
        except Exception:
            return True

    @staticmethod
    def reset() -> None:
        """Clear the 'setup_done' flag so the wizard runs again next launch."""
        p = Path.home() / ".noctis" / "config.json"
        try:
            cfg: Dict[str, object] = {}
            if p.exists():
                cfg = json.loads(p.read_text(encoding="utf-8"))
            cfg["setup_done"] = False
            p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception:
            pass


# ── Main Application ──────────────────────────────────────────────────────────

class Noctis(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Noctis")
        self.geometry("1100x720")
        self.minsize(800, 550)
        self.configure(bg=BG_WINDOW)
        self.option_add("*tearOff", False)
        self.tk_setPalette(background=BG_WINDOW, foreground=FG_PRIMARY)

        self.font_family = "Consolas"
        self.font_size   = 11

        self.tabs:               List[TabInfo]            = []
        self.current_tab_index:  Optional[int]            = None
        self._ai_mode:           bool                     = False
        self._ai_chat_history:   List[Dict[str, str]]     = []
        self._images:            List[ImageTk.PhotoImage] = []
        self._thinking_pulse_id: Optional[str]            = None

        # theme state — set BEFORE _create_widgets so _menu_data can read it
        self.current_theme = "Dark (Default)"
        self.theme_var     = StringVar(value="Dark (Default)")

        # dropdown state
        self._active_dropdown:      Optional[ModernDropdown] = None
        self._active_dropdown_name: Optional[str]            = None
        self._menu_buttons:         Dict[str, Button]        = {}

        self._create_widgets()
        self._create_keybindings()

        # Close any open dropdown when window is moved / resized
        self.bind("<Configure>", lambda _e: self._close_dropdown(), add=True)

        self.new_tab()
        dark_titlebar(self)
        self._load_theme_preference()

        # AI setup is on-demand — no auto-wizard on startup

    # ── Widget construction ───────────────────────────────────────────────────

    def _create_widgets(self) -> None:

        # ── Custom menu bar (elevated surface) ───────────────────────────────
        self.menubar_frame = Frame(self, bg=BG_SURFACE, height=36)
        self.menubar_frame.pack(side="top", fill="x")
        self.menubar_frame.pack_propagate(False)

        for name, items in self._menu_data().items():
            self._add_menu_button(name, items)

        # 1 px bottom border below menu bar
        _d1 = Frame(self, bg=DIVIDER, height=1)
        _d1.pack(side="top", fill="x")

        # ── Tab bar ────────────────────────────────────────────────────────────
        self.tabs_bar = Frame(self, bg=BG_WINDOW, height=40)
        self.tabs_bar.pack(side="top", fill="x")
        self.tabs_bar.pack_propagate(False)

        # AI toggle — premium sparkle CTA (right)
        self.ai_toggle_btn = Button(
            self.tabs_bar,
            text="✨ AI",
            bg=ACCENT_DARK, fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2",
            padx=16, pady=5,
            activebackground=ACCENT_SUBTLE,
            activeforeground="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground=ACCENT_DARK,
            highlightcolor=ACCENT,
            command=self.toggle_ai,
        )
        self.ai_toggle_btn.pack(side="right", padx=(0, 10), pady=8)
        self.ai_toggle_btn.bind(
            "<Enter>",
            lambda e: self.ai_toggle_btn.config(
                bg=ACCENT_SUBTLE, highlightbackground=ACCENT
            ) if not self._ai_mode else None,
        )
        self.ai_toggle_btn.bind(
            "<Leave>",
            lambda e: self.ai_toggle_btn.config(
                bg=ACCENT_DARK, highlightbackground=ACCENT_DARK
            ) if not self._ai_mode else None,
        )

        # Tabs container (left) — new_tab_button lives inside here too
        self.tabs_container = Frame(self.tabs_bar, bg=BG_WINDOW)
        self.tabs_container.pack(side="left", fill="both", expand=True, padx=(8, 0))

        # New tab "+" — inline after the last tab (Chrome / Firefox style)
        self.new_tab_button = Button(
            self.tabs_container,          # ← inside tabs_container, not tabs_bar
            text="+",
            bg=BG_WINDOW, fg=ACCENT,
            font=("Segoe UI", 14, "bold"),
            relief="flat", cursor="hand2",
            padx=10, pady=4,
            activebackground=BG_ELEVATED,
            activeforeground=ACCENT_HOVER,
            bd=0,
            command=self.new_tab,
        )
        self.new_tab_button.pack(side="left", padx=(2, 4), pady=(4, 0))
        self.new_tab_button.bind(
            "<Enter>", lambda e: self.new_tab_button.config(bg=BG_ELEVATED)
        )
        self.new_tab_button.bind(
            "<Leave>", lambda e: self.new_tab_button.config(bg=BG_WINDOW)
        )

        _d2 = Frame(self, bg=DIVIDER, height=1)
        _d2.pack(side="top", fill="x")

        # ── Status bar ─────────────────────────────────────────────────────────
        _d3 = Frame(self, bg=DIVIDER, height=1)
        _d3.pack(side="bottom", fill="x")

        self.statusbar = Frame(self, bg=BG_WINDOW, height=26)
        self.statusbar.pack(side="bottom", fill="x")
        self.statusbar.pack_propagate(False)

        _sl = dict(bg=BG_WINDOW, font=("Segoe UI", 9))

        self.status_pos_label = Label(
            self.statusbar, text="Ln 1, Col 1",
            fg=FG_SECONDARY, padx=12, pady=4, **_sl,
        )
        self.status_pos_label.pack(side="left")

        _sep0 = Label(self.statusbar, text="│", fg=FG_TERTIARY, padx=0, pady=4, **_sl)
        _sep0.pack(side="left")

        self.status_words_label = Label(
            self.statusbar, text="0 words",
            fg=FG_SECONDARY, padx=8, pady=4, **_sl,
        )
        self.status_words_label.pack(side="left")

        self.status_ai_label = Label(
            self.statusbar,
            text=f"\U0001f512 Local  {AI_MODEL}",
            fg=FG_TERTIARY, padx=12, pady=4, **_sl,
        )
        self.status_ai_label.pack(side="right")

        _sep1 = Label(self.statusbar, text="│", fg=FG_TERTIARY, padx=0, pady=4, **_sl)
        _sep1.pack(side="right")
        _lbl_enc = Label(self.statusbar, text="UTF-8", fg=FG_SECONDARY, padx=10, pady=4, **_sl)
        _lbl_enc.pack(side="right")
        _sep2 = Label(self.statusbar, text="│", fg=FG_TERTIARY, padx=0, pady=4, **_sl)
        _sep2.pack(side="right")
        _lbl_le = Label(self.statusbar, text="CRLF", fg=FG_SECONDARY, padx=10, pady=4, **_sl)
        _lbl_le.pack(side="right")
        _sep3 = Label(self.statusbar, text="│", fg=FG_TERTIARY, padx=0, pady=4, **_sl)
        _sep3.pack(side="right")

        # Store references for apply_theme
        self._dividers            = [_d1, _d2, _d3]
        self._status_sep_labels   = [_sep0, _sep1, _sep2, _sep3]
        self._status_static_labels = [_lbl_enc, _lbl_le]

        # ── Editor container ───────────────────────────────────────────────────
        self.editor_container = Frame(self, bg=BG_WINDOW)
        self.editor_container.pack(fill="both", expand=True)

    # ── Custom menu bar helpers ───────────────────────────────────────────────

    def _menu_data(self) -> Dict[str, List[Dict]]:
        """Return the full menu structure as a dict of {name: [item, ...]}."""
        return {
            "File": [
                {"type": "command", "icon": "📄", "label": "New Tab",
                 "shortcut": "Ctrl+N",       "command": self.new_tab},
                {"type": "command", "icon": "📂", "label": "Open…",
                 "shortcut": "Ctrl+O",       "command": self.open_file},
                {"type": "command", "icon": "💾", "label": "Save",
                 "shortcut": "Ctrl+S",       "command": self.save_file},
                {"type": "command", "icon": "💾", "label": "Save As…",
                 "shortcut": "Ctrl+⇧+S",    "command": self.save_file_as},
                {"type": "separator"},
                {"type": "command", "icon": "🚪", "label": "Exit",
                 "shortcut": "",             "command": self.on_exit},
            ],
            "Edit": [
                {"type": "command", "icon": "↩",  "label": "Undo",
                 "shortcut": "Ctrl+Z",       "command": self._editor_undo},
                {"type": "command", "icon": "↪",  "label": "Redo",
                 "shortcut": "Ctrl+Y",       "command": self._editor_redo},
                {"type": "separator"},
                {"type": "command", "icon": "✂",  "label": "Cut",
                 "shortcut": "Ctrl+X",       "command": self._editor_cut},
                {"type": "command", "icon": "📋", "label": "Copy",
                 "shortcut": "Ctrl+C",       "command": self._editor_copy},
                {"type": "command", "icon": "📌", "label": "Paste",
                 "shortcut": "Ctrl+V",       "command": self._editor_paste},
                {"type": "separator"},
                {"type": "command", "icon": "☰",  "label": "Select All",
                 "shortcut": "Ctrl+A",       "command": self._editor_select_all},
                {"type": "separator"},
                {"type": "command", "icon": "🔍", "label": "Find & Replace",
                 "shortcut": "Ctrl+F",       "command": self.open_find_replace},
            ],
            "View": [
                {"type": "command", "icon": "＋", "label": "Zoom In",
                 "shortcut": "Ctrl+=",       "command": self._zoom_in},
                {"type": "command", "icon": "－", "label": "Zoom Out",
                 "shortcut": "Ctrl+−",       "command": self._zoom_out},
                {"type": "command", "icon": "⊙",  "label": "Restore Zoom",
                 "shortcut": "Ctrl+0",       "command": self._zoom_reset},
                {"type": "separator"},
                {"type": "command", "icon": "↵",  "label": "Word Wrap",
                 "shortcut": "",             "command": self.toggle_word_wrap},
            ],
            "Format": [
                {"type": "command", "icon": "🔤", "label": "Font…",
                 "shortcut": "",             "command": self.open_font_picker},
                {"type": "separator"},
                {"type": "command", "icon": "🖼", "label": "Insert Image",
                 "shortcut": "Ctrl+⇧+I",    "command": self.insert_image},
            ],
            "Themes": self._themes_items,   # callable — rebuilt each open
            "AI": [
                {"type": "command", "icon": "🆘",  "label": "Crisis Resources",
                 "shortcut": "",             "command": self.show_crisis_resources},
                {"type": "separator"},
                {"type": "command", "icon": "⚙",  "label": "Setup AI Model",
                 "shortcut": "",             "command": self.setup_ai_model},
                {"type": "separator"},
                {"type": "command", "icon": "✨",  "label": "Toggle AI Mode",
                 "shortcut": "Ctrl+`",       "command": self.toggle_ai},
                {"type": "separator"},
                {"type": "command", "icon": "💬", "label": "Ask AI",
                 "shortcut": "",             "command": self.ask_ai},
                {"type": "command", "icon": "📊", "label": "Summarize Note",
                 "shortcut": "",             "command": self.summarize_note},
                {"type": "command", "icon": "✍",  "label": "Fix Grammar",
                 "shortcut": "",             "command": self.fix_grammar},
            ],
            "Help": [
                {"type": "command", "icon": "ℹ",  "label": "About Noctis",
                 "shortcut": "",             "command": self.show_about},
                {"type": "separator"},
                {"type": "command", "icon": "⚙",  "label": "Re-run Setup Wizard",
                 "shortcut": "",             "command": self._rerun_setup},
            ],
        }

    def _add_menu_button(self, label: str, items) -> None:
        btn = Button(
            self.menubar_frame,
            text=label,
            bg=BG_SURFACE, fg=FG_SECONDARY,
            activebackground=BG_ELEVATED, activeforeground=FG_PRIMARY,
            font=("Segoe UI", 10),
            relief="flat", bd=0,
            padx=14, pady=8,
            cursor="hand2",
        )

        def _show(b=btn, n=label, items_src=items):
            # items_src may be a list or a zero-arg callable (for dynamic menus)
            resolved = items_src() if callable(items_src) else items_src
            self._show_dropdown(b, n, resolved)

        btn.config(command=_show)
        btn.bind("<Enter>", lambda _e, b=btn: self._menu_btn_enter(b, label))
        btn.bind("<Leave>", lambda _e, b=btn: self._menu_btn_leave(b, label))
        btn.pack(side="left")
        self._menu_buttons[label] = btn

    def _menu_btn_enter(self, btn: Button, name: str) -> None:
        btn.config(bg=BG_ELEVATED, fg=FG_PRIMARY)

    def _menu_btn_leave(self, btn: Button, name: str) -> None:
        if self._active_dropdown_name == name:
            return   # keep highlighted while its dropdown is open
        btn.config(bg=BG_SURFACE, fg=FG_SECONDARY)

    def _show_dropdown(self, btn: Button, name: str, items: List[Dict]) -> None:
        # Toggle: clicking the open menu's button closes it
        if self._active_dropdown_name == name and self._active_dropdown:
            self._close_dropdown()
            return

        self._close_dropdown()

        # Highlight the owning button
        btn.config(bg=BG_ELEVATED, fg=FG_PRIMARY)
        self._active_dropdown_name = name

        x = btn.winfo_rootx()
        y = btn.winfo_rooty() + btn.winfo_height()

        self._active_dropdown = ModernDropdown(
            self, items, x, y,
            on_close=lambda b=btn: self._on_dropdown_closed(b),
        )

    def _close_dropdown(self) -> None:
        if self._active_dropdown:
            try:
                self._active_dropdown.close()
            except Exception:
                pass
            self._active_dropdown      = None
            self._active_dropdown_name = None

    def _on_dropdown_closed(self, btn: Button) -> None:
        """Called by ModernDropdown.close() via on_close callback."""
        btn.config(bg=BG_SURFACE, fg=FG_SECONDARY)
        self._active_dropdown      = None
        self._active_dropdown_name = None

    # ── Tab Management ────────────────────────────────────────────────────────

    def new_tab(self, file_path: Optional[Path] = None, content: str = "") -> None:
        title = file_path.name if file_path else "Untitled"

        tab_frame = Frame(self.editor_container, bg=BG_WINDOW)

        text_widget = Text(
            tab_frame,
            bg=BG_WINDOW, fg=FG_PRIMARY,
            insertbackground=CURSOR_CLR,
            selectbackground=SELECT_BG,
            selectforeground=FG_PRIMARY,
            font=(self.font_family, self.font_size),
            wrap="word",
            relief="flat", bd=0,
            padx=24, pady=20,
            spacing1=4, spacing2=1, spacing3=4,
            cursor="xterm",
            undo=True,
        )

        scrollbar = tk.Scrollbar(
            tab_frame,
            bg=BG_WINDOW, troughcolor=BG_WINDOW,
            activebackground=BORDER,
            highlightthickness=0,
            relief="flat", width=8, bd=0,
        )
        text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=text_widget.yview)

        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True)

        text_widget.insert("1.0", content)
        text_widget.edit_modified(False)

        self._ensure_ai_tags(text_widget)
        text_widget.bind("<<Modified>>",    self._on_text_modified)
        text_widget.bind("<KeyRelease>",    self._update_status_from_event)
        text_widget.bind("<ButtonRelease>", self._update_status_from_event)
        text_widget.bind("<Control-v>",     self._paste_handler)
        text_widget.bind("<Control-V>",     self._paste_handler)
        text_widget.bind("<Return>",        self._handle_enter)

        # ── tab strip (premium icon + title + dot + close layout) ────────────
        idx = len(self.tabs)

        # Outermost container — manages the bottom indicator bar
        # Pack *before* new_tab_button so + always stays at the end
        tab_outer = Frame(self.tabs_container, bg=BG_WINDOW)
        tab_outer.pack(side="left", padx=(0, 2), pady=(4, 0),
                       before=self.new_tab_button)

        # Inner row holds all visible tab content
        tab_inner = Frame(tab_outer, bg=BG_WINDOW)
        tab_inner.pack(side="top", fill="x", padx=0, pady=(2, 2))

        # File icon: 📄 saved, 📝 unsaved
        icon_lbl = Label(
            tab_inner,
            text="📄",
            bg=BG_WINDOW, fg=FG_SECONDARY,
            font=("Segoe UI", 9),
        )
        icon_lbl.pack(side="left", padx=(10, 3))

        # Title
        title_lbl = Label(
            tab_inner,
            text=self._truncate(title),
            bg=BG_WINDOW, fg=FG_SECONDARY,
            font=("Segoe UI", 9),
            anchor="w",
        )
        title_lbl.pack(side="left")

        # Unsaved dot — green ● (invisible when saved)
        dot_lbl = Label(
            tab_inner,
            text="●",
            bg=BG_WINDOW, fg=BG_WINDOW,   # hidden until unsaved
            font=("Segoe UI", 6),
        )
        dot_lbl.pack(side="left", padx=(5, 0))

        # Close ×
        close_button = Button(
            tab_inner,
            text="×",
            bg=BG_WINDOW, fg=BG_WINDOW,   # hidden until hover / active
            font=("Segoe UI", 11),
            relief="flat", cursor="hand2",
            padx=5, pady=2,
            activebackground="#3a1c1c", activeforeground=CLOSE_RED,
            bd=0,
            command=lambda i=idx: self.close_tab(i),
        )
        close_button.pack(side="left", padx=(4, 8))

        # 2 px bottom accent bar (green when active)
        indicator = Frame(tab_outer, bg=BG_WINDOW, height=2)
        indicator.pack(side="bottom", fill="x")

        # mutable back-reference so hover closures can read tab.unsaved
        _tab_ref: List[Optional[TabInfo]] = [None]
        _inner_all = (tab_outer, tab_inner, icon_lbl, title_lbl, dot_lbl)

        def _set_bg(bg: str) -> None:
            for w in _inner_all:
                w.config(bg=bg)
            close_button.config(bg=bg)

        def _dot_fg(bg: str) -> str:
            ti = _tab_ref[0]
            return ACCENT if (ti and ti.unsaved) else bg

        def _on_enter(_e, i=idx) -> None:
            if i != self.current_tab_index:
                _set_bg(BG_SURFACE)
                title_lbl.config(fg=FG_PRIMARY)
                indicator.config(bg=BG_SURFACE)
                close_button.config(fg=FG_SECONDARY)
                dot_lbl.config(fg=_dot_fg(BG_SURFACE))

        def _on_leave(_e, i=idx) -> None:
            if i != self.current_tab_index:
                _set_bg(BG_WINDOW)
                title_lbl.config(fg=FG_SECONDARY)
                indicator.config(bg=BG_WINDOW)
                close_button.config(fg=BG_WINDOW)
                dot_lbl.config(fg=_dot_fg(BG_WINDOW))

        for w in _inner_all:
            w.bind("<Enter>",    _on_enter)
            w.bind("<Leave>",    _on_leave)
            w.bind("<Button-1>", lambda _e, i=idx: self.switch_tab(i))

        close_button.bind("<Enter>", lambda _e: close_button.config(fg=CLOSE_RED))
        close_button.bind(
            "<Leave>",
            lambda _e, i=idx: close_button.config(
                fg=FG_SECONDARY if i == self.current_tab_index else BG_WINDOW
            ),
        )

        tab_info = TabInfo(
            frame=tab_frame,
            button=title_lbl,             # Label kept as .button for compat
            close_button=close_button,
            indicator=indicator,
            text=text_widget,
            file_path=file_path,
            title=title,
            unsaved=bool(content),
            tab_outer=tab_outer,
            tab_inner=tab_inner,
            icon_label=icon_lbl,
            dot_label=dot_lbl,
            scrollbar=scrollbar,
        )
        _tab_ref[0] = tab_info           # connect closure back-reference
        self.tabs.append(tab_info)
        self.switch_tab(len(self.tabs) - 1)

    # ── tab visual-state helpers ──────────────────────────────────────────────

    def _tab_apply_inactive(self, tab: TabInfo) -> None:
        bg = BG_WINDOW
        for w in (tab.tab_outer, tab.tab_inner, tab.icon_label, tab.dot_label):
            if w is not None:
                w.config(bg=bg)
        tab.button.config(bg=bg, fg=FG_SECONDARY)
        tab.indicator.config(bg=bg)
        tab.close_button.config(bg=bg, fg=bg)
        if tab.dot_label is not None:
            tab.dot_label.config(fg=ACCENT if tab.unsaved else bg)

    def _tab_apply_active(self, tab: TabInfo) -> None:
        bg = BG_ELEVATED
        for w in (tab.tab_outer, tab.tab_inner, tab.icon_label, tab.dot_label):
            if w is not None:
                w.config(bg=bg)
        tab.button.config(bg=bg, fg=FG_PRIMARY)
        tab.indicator.config(bg=ACCENT)
        tab.close_button.config(bg=bg, fg=FG_SECONDARY)
        if tab.dot_label is not None:
            tab.dot_label.config(fg=ACCENT if tab.unsaved else bg)

    def switch_tab(self, index: int) -> None:
        if index < 0 or index >= len(self.tabs):
            return

        if self.current_tab_index is not None:
            prev = self.tabs[self.current_tab_index]
            prev.frame.pack_forget()
            self._tab_apply_inactive(prev)

        self.current_tab_index = index
        tab = self.tabs[index]
        tab.frame.pack(fill="both", expand=True)
        self._tab_apply_active(tab)
        self._update_status()

    def close_tab(self, index: Optional[int] = None) -> None:
        if not self.tabs:
            return
        if index is None:
            index = self.current_tab_index
        if index is None or index < 0 or index >= len(self.tabs):
            return

        tab = self.tabs[index]
        if tab.unsaved and not self._confirm_discard_changes(tab.title):
            return

        tab.frame.destroy()
        # destroy the outermost tab strip container (tab_outer)
        outer = tab.tab_outer if tab.tab_outer is not None else tab.button.master.master
        outer.destroy()
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

    # ── File Operations ───────────────────────────────────────────────────────

    def open_file(self) -> None:
        s = filedialog.askopenfilename(
            title="Open Note",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not s:
            return
        path = Path(s)
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
        else:
            self._write_tab_to_path(tab, tab.file_path)

    def save_file_as(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return
        s = filedialog.asksaveasfilename(
            title="Save Note As",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if s:
            self._write_tab_to_path(tab, Path(s))

    def _write_tab_to_path(self, tab: TabInfo, path: Path) -> None:
        content = tab.text.get("1.0", "end-1c")
        try:
            path.write_text(content, encoding="utf-8")
        except OSError:
            return
        tab.file_path = path
        tab.title     = path.name
        tab.unsaved   = False
        self._update_tab_title(tab)

    # ── Edit commands ─────────────────────────────────────────────────────────

    def _editor_undo(self) -> None:
        tab = self._get_current_tab()
        if tab:
            try: tab.text.edit_undo()
            except Exception: pass

    def _editor_redo(self) -> None:
        tab = self._get_current_tab()
        if tab:
            try: tab.text.edit_redo()
            except Exception: pass

    def _editor_cut(self)        -> None:
        tab = self._get_current_tab()
        if tab: tab.text.event_generate("<<Cut>>")

    def _editor_copy(self)       -> None:
        tab = self._get_current_tab()
        if tab: tab.text.event_generate("<<Copy>>")

    def _editor_paste(self)      -> None:
        tab = self._get_current_tab()
        if tab: tab.text.event_generate("<<Paste>>")

    def _editor_select_all(self) -> None:
        tab = self._get_current_tab()
        if tab:
            tab.text.tag_add("sel", "1.0", "end-1c")
            tab.text.focus_set()

    # ── View / Zoom ───────────────────────────────────────────────────────────

    def zoom(self, direction: int) -> None:
        """Unified zoom entry-point: +1 in, -1 out, 0 reset."""
        if direction == 0:
            self._zoom_reset()
        elif direction > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _zoom_in(self) -> None:
        if self.font_size < 28:
            self.font_size += 1
            self._apply_font_all()

    def _zoom_out(self) -> None:
        if self.font_size > 8:
            self.font_size -= 1
            self._apply_font_all()

    def _zoom_reset(self) -> None:
        self.font_size = 11
        self._apply_font_all()

    def _apply_font_all(self) -> None:
        for t in self.tabs:
            t.text.configure(font=(self.font_family, self.font_size))

    def toggle_word_wrap(self) -> None:
        tab = self._get_current_tab()
        if tab:
            new = "none" if tab.text.cget("wrap") == "word" else "word"
            tab.text.configure(wrap=new)

    # ── Find & Replace ────────────────────────────────────────────────────────

    def open_find_replace(self) -> None:
        if not self._get_current_tab():
            return

        win = _make_dialog(self, "Find & Replace", width=480, height=196)
        win.grab_set()

        outer = Frame(win, bg=BG_SURFACE)
        outer.pack(fill="both", expand=True, padx=20, pady=16)

        _lbl = dict(bg=BG_SURFACE, fg=FG_PRIMARY, font=("Segoe UI", 9),
                    width=8, anchor="e")

        Label(outer, text="Find",    **_lbl).grid(row=0, column=0, sticky="e", pady=6)
        find_e = _make_entry(outer, width=34)
        find_e.grid(row=0, column=1, columnspan=3, sticky="ew", padx=(10, 0), pady=6)

        Label(outer, text="Replace", **_lbl).grid(row=1, column=0, sticky="e", pady=6)
        repl_e = _make_entry(outer, width=34)
        repl_e.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(10, 0), pady=6)

        btn_f = Frame(outer, bg=BG_SURFACE)
        btn_f.grid(row=2, column=0, columnspan=4, sticky="e", pady=(12, 0))

        def _fn():  self._find_text(find_e.get(), forward=True)
        def _fp():  self._find_text(find_e.get(), forward=False)
        def _r():   self._replace_current(find_e.get(), repl_e.get())
        def _ra():  self._replace_all(find_e.get(), repl_e.get())

        for lbl, cmd, prim in [
            ("Next", _fn, True), ("Previous", _fp, False),
            ("Replace", _r, False), ("Replace All", _ra, False),
        ]:
            _make_btn(btn_f, lbl, cmd, primary=prim).pack(side="left", padx=3)

        outer.columnconfigure(1, weight=1)
        find_e.focus_set()

    def _find_text(self, pattern: str, forward: bool = True) -> None:
        tab = self._get_current_tab()
        if not tab or not pattern:
            return
        text = tab.text
        text.tag_remove("search_highlight", "1.0", "end")
        idx = (
            text.search(pattern, "insert", stopindex="end")
            if forward else
            text.search(pattern, "1.0", stopindex="insert", backwards=True)
        )
        if not idx:
            return
        end = f"{idx}+{len(pattern)}c"
        text.tag_add("search_highlight", idx, end)
        text.tag_config("search_highlight", background=ACCENT, foreground=BG_WINDOW)
        text.mark_set("insert", end if forward else idx)
        text.see(idx)

    def _replace_current(self, pattern: str, replacement: str) -> None:
        tab = self._get_current_tab()
        if not tab or not pattern:
            return
        text  = tab.text
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
        if not tab or not pattern:
            return
        text = tab.text
        pos  = "1.0"
        while True:
            idx = text.search(pattern, pos, stopindex="end")
            if not idx:
                break
            end = f"{idx}+{len(pattern)}c"
            text.delete(idx, end)
            text.insert(idx, replacement)
            pos = f"{idx}+{len(replacement)}c"
        self._mark_unsaved(tab)

    # ── Font Picker ───────────────────────────────────────────────────────────

    def open_font_picker(self) -> None:
        win = _make_dialog(self, "Font", width=440, height=290, resizable=False)
        win.grab_set()

        outer = Frame(win, bg=BG_SURFACE)
        outer.pack(fill="both", expand=True, padx=20, pady=16)

        _lbl = dict(bg=BG_SURFACE, fg=FG_PRIMARY, font=("Segoe UI", 9), anchor="w")

        Label(outer, text="Font Family", **_lbl).grid(row=0, column=0, sticky="w", pady=6)

        families = ["Consolas", "Cascadia Code", "Fira Code", "JetBrains Mono",
                    "Courier New", "Lucida Console"]
        if self.font_family not in families:
            families.insert(0, self.font_family)

        font_var = StringVar(value=self.font_family)
        om = OptionMenu(outer, font_var, *families)
        om.config(
            bg=BG_ELEVATED, fg=FG_PRIMARY,
            activebackground=HOVER_BG, activeforeground=FG_PRIMARY,
            relief="flat", highlightthickness=1,
            highlightbackground=BORDER, font=("Segoe UI", 9), bd=0,
        )
        om["menu"].config(
            bg=BG_ELEVATED, fg=FG_PRIMARY,
            activebackground=HOVER_BG, activeforeground=FG_PRIMARY,
            font=("Segoe UI", 9),
        )
        om.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=6)

        Label(outer, text="Size", **_lbl).grid(row=1, column=0, sticky="w", pady=6)

        size_var = IntVar(value=self.font_size)
        sp = Spinbox(
            outer, from_=8, to=28, textvariable=size_var, width=6,
            bg=BG_ELEVATED, fg=FG_PRIMARY,
            buttonbackground=BG_ELEVATED, insertbackground=FG_PRIMARY,
            relief="flat", highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
            font=("Segoe UI", 9),
        )
        sp.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=6)

        Label(outer, text="Preview", bg=BG_SURFACE, fg=FG_TERTIARY,
              font=("Segoe UI", 8)).grid(row=2, column=0, columnspan=2,
                                          sticky="w", pady=(10, 2))
        preview = Text(
            outer, height=3,
            bg=BG_WINDOW, fg=FG_PRIMARY,
            font=(self.font_family, self.font_size),
            wrap="word", relief="flat", bd=0, padx=10, pady=8,
            highlightthickness=1, highlightbackground=BORDER,
        )
        preview.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 12))
        preview.insert("1.0", "The quick brown fox\nThis space is just for you.")
        preview.configure(state="disabled")

        def _upd(*_):
            try: sz = int(size_var.get())
            except (ValueError, tk.TclError): sz = self.font_size
            preview.configure(state="normal", font=(font_var.get(), sz))
            preview.configure(state="disabled")

        font_var.trace_add("write", _upd)
        size_var.trace_add("write", _upd)

        br = Frame(outer, bg=BG_SURFACE)
        br.grid(row=4, column=0, columnspan=2, sticky="e")

        def _apply():
            try:
                self.font_family = font_var.get()
                self.font_size   = int(size_var.get())
                self._apply_font_all()
                win.destroy()
            except Exception:
                pass

        _make_btn(br, "Cancel", win.destroy).pack(side="left", padx=(0, 8))
        _make_btn(br, "Apply",  _apply, primary=True).pack(side="left")

        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(3, weight=1)

    # ── Image Insertion ───────────────────────────────────────────────────────

    def _paste_handler(self, event=None):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is not None and hasattr(img, "size"):
                max_w = 600
                if img.width > max_w:
                    img = img.resize(
                        (max_w, int(img.height * max_w / img.width)),
                        Image.LANCZOS,
                    )
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
        except Exception as exc:
            print(f"Paste error: {exc}")
        return None

    def insert_image(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.webp"),
                       ("All Files", "*.*")],
        )
        if not path:
            return
        img   = Image.open(path)
        max_w = 600
        if img.width > max_w:
            img = img.resize(
                (max_w, int(img.height * max_w / img.width)),
                Image.LANCZOS,
            )
        photo = ImageTk.PhotoImage(img)
        self._images.append(photo)
        tab.text.image_create("insert", image=photo)
        tab.text.insert("insert", "\n")
        self._mark_unsaved(tab)

    # ── AI ────────────────────────────────────────────────────────────────────

    def _ensure_ai_tags(self, text: Text) -> None:
        text.tag_configure("separator",
                           foreground=BORDER)
        text.tag_configure("ai_label",
                           foreground=ACCENT,
                           font=("Consolas", 12, "bold"))
        text.tag_configure("user_msg",
                           foreground=ACCENT,
                           font=("Consolas", self.font_size, "bold"))
        text.tag_configure("ai_reply",
                           foreground=FG_PRIMARY)
        text.tag_configure("thinking",
                           foreground=FG_SECONDARY,
                           font=("Consolas", self.font_size, "italic"))

    # ── Ollama / model checks (fast, non-blocking) ───────────────────────────

    def _ollama_running(self) -> bool:
        """Return True if the Ollama HTTP API answers within 1 s."""
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=1)
            return r.status_code == 200
        except Exception:
            return False

    def _model_installed(self) -> bool:
        """Return True if noctis-ai-v1 is listed by Ollama."""
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=1)
            if r.status_code != 200:
                return False
            names = [m.get("name", "") for m in r.json().get("models", [])]
            return any(AI_MODEL in n for n in names)
        except Exception:
            return False

    def _show_setup_prompt(self, title: str, message: str,
                           show_setup_btn: bool = False) -> bool:
        """Modal info / confirm dialog.  Returns True if user chose 'Setup Now'."""
        result: Dict[str, bool] = {"answer": False}

        win = _make_dialog(self, title, width=440, height=210)
        win.grab_set()
        Frame(win, bg=ACCENT_DARK, height=2).pack(side="top", fill="x")
        Label(
            win, text=message,
            bg=BG_SURFACE, fg=FG_PRIMARY,
            font=("Segoe UI", 9),
            justify="left", wraplength=396,
        ).pack(padx=22, pady=(16, 12), anchor="w")

        br = Frame(win, bg=BG_SURFACE)
        br.pack(padx=22, pady=(0, 16), anchor="e")

        def _set(v: bool):
            result["answer"] = v
            win.destroy()

        _make_btn(br, "Cancel", lambda: _set(False)).pack(side="left", padx=(0, 8))
        if show_setup_btn:
            _make_btn(br, "Setup Now", lambda: _set(True),
                      primary=True).pack(side="left")

        self.wait_window(win)
        return result["answer"]

    def setup_ai_model(self) -> None:
        """Launch the AI setup wizard on demand from the AI menu."""
        if not self._ollama_running():
            self._show_setup_prompt(
                "Ollama Not Running",
                "Ollama is not installed or not currently running.\n\n"
                "To use AI features:\n"
                "  1.  Install Ollama from  ollama.com\n"
                "  2.  Start it (it runs silently in the system tray)\n"
                "  3.  Return here and choose AI → Setup AI Model",
            )
            return

        if self._model_installed():
            self._show_messagebox(
                "AI Already Ready",
                f"The Noctis AI model ({AI_MODEL}) is already installed.\n\n"
                "Click the ✨ AI button or press Ctrl+` to start chatting.",
            )
            return

        # Launch wizard
        SetupWizard.reset()          # ensure wizard considers setup incomplete
        self.withdraw()
        wiz = SetupWizard(self)
        self.wait_window(wiz)
        self.deiconify()

    def toggle_ai(self) -> None:
        """Toggle AI mode on/off; status checks run in a background thread."""
        if self._ai_mode:
            self._ai_turn_off()
            return

        # Show a subtle loading indicator while checking in background
        self.ai_toggle_btn.config(text="AI ⏳")

        def _check():
            ollama_ok = self._ollama_running()

            if not ollama_ok:
                def _on_no_ollama():
                    self.ai_toggle_btn.config(text="✨ AI")
                    if self._show_setup_prompt(
                        "Ollama Not Running",
                        "Ollama is not running.\n\n"
                        "To use AI features:\n"
                        "  1.  Install Ollama from  ollama.com\n"
                        "  2.  Start it (it runs silently in the system tray)\n"
                        "  3.  Choose  AI → Setup AI Model\n\n"
                        "Would you like to open the Setup Wizard now?",
                        show_setup_btn=True,
                    ):
                        self.setup_ai_model()
                self.after(0, _on_no_ollama)
                return

            model_ok = self._model_installed()

            if not model_ok:
                def _on_no_model():
                    self.ai_toggle_btn.config(text="✨ AI")
                    if self._show_setup_prompt(
                        "AI Model Not Installed",
                        f"{AI_MODEL} is not installed yet.\n\n"
                        "The setup wizard will download the model (~2 GB).\n"
                        "This takes 5–10 minutes the first time.\n\n"
                        "Would you like to set it up now?",
                        show_setup_btn=True,
                    ):
                        self.setup_ai_model()
                self.after(0, _on_no_model)
                return

            # Everything ready — activate AI on the main thread
            self.after(0, self._ai_turn_on)

        threading.Thread(target=_check, daemon=True).start()

    def _ai_turn_on(self) -> None:
        if self._ai_mode:
            return
        tab = self._get_current_tab()
        if not tab:
            return
        self._ai_mode = True

        self.ai_toggle_btn.config(
            bg=ACCENT, fg=BG_WINDOW,
            activebackground=ACCENT_HOVER, activeforeground=BG_WINDOW,
            text="✨ AI  ON",
            highlightbackground=ACCENT_HOVER,
        )
        self.status_ai_label.config(text=f"✨ AI Active  {AI_MODEL}", fg=ACCENT)

        text = tab.text
        current = text.get("1.0", "end-1c")
        if current.strip():
            text.insert("end", "\n" if current.endswith("\n") else "\n\n")

        text.insert("end", _AI_SEP + "\n")
        sep_idx = text.search(_AI_SEP, "end", backwards=True, stopindex="1.0")
        if sep_idx:
            text.tag_add("separator", sep_idx, f"{sep_idx}+{len(_AI_SEP)}c")

        text.insert("end", "Noctis AI\n\n")
        h_idx = text.search("Noctis AI", "end", backwards=True, stopindex="1.0")
        if h_idx:
            text.tag_add("ai_label", h_idx, f"{h_idx}+9c")

        text.insert("end", ">>> ")
        p_idx = text.search(">>> ", "end", backwards=True, stopindex="1.0")
        if p_idx:
            text.tag_add("user_msg", p_idx, f"{p_idx}+4c")

        text.see("end")
        text.mark_set("insert", "end")
        text.focus_set()
        self._ai_chat_history = []

    def _ai_turn_off(self) -> None:
        self._ai_mode = False
        if self._thinking_pulse_id:
            self.after_cancel(self._thinking_pulse_id)
            self._thinking_pulse_id = None

        self.ai_toggle_btn.config(
            bg=ACCENT_DARK, fg="#ffffff",
            activebackground=ACCENT_SUBTLE, activeforeground="#ffffff",
            text="✨ AI",
            highlightbackground=ACCENT_DARK,
        )
        self.status_ai_label.config(
            text=f"\U0001f512 Local  {AI_MODEL}", fg=FG_TERTIARY,
        )
        self._ai_chat_history = []
        tab = self._get_current_tab()
        if tab:
            tab.text.focus_set()

    def _handle_enter(self, event=None) -> Optional[str]:
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
            return "break"

        text.mark_set("insert", "insert lineend")
        text.insert("end", "\n\n")
        think_start = text.index("end-1c")
        text.insert("end", "  thinking...")
        text.tag_add("thinking", think_start, text.index("end-1c"))
        text.see("end")

        self._start_thinking_pulse(text, think_start)

        _msg     = msg
        _cleared = [False]
        messages_ctx = (
            [{"role": "system", "content": NOCTIS_SYSTEM_PROMPT}]
            + self._ai_chat_history
        )

        def on_token(token: str) -> None:
            def append() -> None:
                if not _cleared[0]:
                    _cleared[0] = True
                    self._stop_thinking_pulse()
                    t = text.search("  thinking...", "end",
                                    backwards=True, stopindex="1.0")
                    if t:
                        text.delete(t, f"{t}+13c")
                text.insert("end", token)
                text.see("end")
            self.after(0, append)

        def on_done(full_reply: str) -> None:
            def finish() -> None:
                self._stop_thinking_pulse()
                text.insert("end", "\n\n>>> ")
                np = text.search(">>> ", "end", backwards=True, stopindex="1.0")
                if np:
                    text.tag_add("user_msg", np, f"{np}+4c")
                text.see("end")
                text.mark_set("insert", "end")
                if full_reply:
                    self._ai_chat_history += [
                        {"role": "user",      "content": _msg},
                        {"role": "assistant", "content": full_reply},
                    ]
            self.after(0, finish)

        def on_error() -> None:
            def show_err() -> None:
                self._stop_thinking_pulse()
                t = text.search("  thinking...", "end",
                                backwards=True, stopindex="1.0")
                if t:
                    text.delete(t, f"{t}+13c")
                text.insert("end", "Ollama is not running.\nRun: ollama serve")
                text.insert("end", "\n\n>>> ")
                np = text.search(">>> ", "end", backwards=True, stopindex="1.0")
                if np:
                    text.tag_add("user_msg", np, f"{np}+4c")
                text.see("end")
            self.after(0, show_err)

        stream_ollama(msg, messages_ctx, on_token, on_done, on_error)
        return "break"

    # ── Thinking pulse ────────────────────────────────────────────────────────

    def _start_thinking_pulse(self, text_widget: Text, _start: str) -> None:
        shades = [FG_SECONDARY, FG_TERTIARY, FG_SECONDARY, "#9ba5b0"]
        step   = [0]

        def _tick() -> None:
            if not self._ai_mode:
                return
            if not text_widget.search("  thinking...", "end",
                                      backwards=True, stopindex="1.0"):
                return
            text_widget.tag_configure("thinking",
                                      foreground=shades[step[0] % len(shades)])
            step[0] += 1
            self._thinking_pulse_id = self.after(420, _tick)

        _tick()

    def _stop_thinking_pulse(self) -> None:
        if self._thinking_pulse_id:
            self.after_cancel(self._thinking_pulse_id)
            self._thinking_pulse_id = None

    # ── AI non-streaming requests ─────────────────────────────────────────────

    def _run_ai_request(
        self,
        system_prompt: str,
        user_text:     str,
        on_success:    Callable[[str], None],
        on_error:      Optional[Callable[[str], None]] = None,
    ) -> None:
        def worker() -> None:
            try:
                prompt   = f"{system_prompt}\n\n---\n\n{user_text.strip()}"
                response = requests.post(
                    AI_URL,
                    json={"model": AI_MODEL, "prompt": prompt, "stream": False},
                    timeout=300,
                )
                response.raise_for_status()
                result = response.json().get("response", "").strip()
                if not result:
                    raise ValueError("Empty response")
            except requests.RequestException:
                msg = "Start Ollama first: run 'ollama serve' in terminal"
                self.after(0, lambda: self._show_messagebox("Ollama Offline", msg))
                if on_error:
                    self.after(0, lambda: on_error(msg))
                return
            except Exception as exc:
                if on_error:
                    err = f"AI error: {exc}"
                    self.after(0, lambda: on_error(err))
                return
            self.after(0, lambda: on_success(result))

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
        loading = self._show_loading_popup("Summarizing your note…")

        def on_done(s: str) -> None:
            loading.destroy()
            self._show_ai_response("Summary", s)

        def on_err(_: str) -> None:
            loading.destroy()

        self._run_ai_request(
            "Summarize this note in a gentle, supportive way. "
            "Highlight key feelings and any small next steps.",
            content, on_done, on_err,
        )

    def fix_grammar(self) -> None:
        tab = self._get_current_tab()
        if not tab or not tab.text.tag_ranges("sel"):
            return
        selected = tab.text.get("sel.first", "sel.last").strip()
        if not selected:
            return
        loading = self._show_loading_popup("Fixing grammar…")

        def on_done(fixed: str) -> None:
            loading.destroy()
            tab.text.delete("sel.first", "sel.last")
            tab.text.insert("insert", fixed)
            self._mark_unsaved(tab)

        def on_err(_: str) -> None:
            loading.destroy()

        self._run_ai_request(
            "Improve the grammar and spelling of this text while keeping "
            "the original tone and meaning. Return only the corrected text.",
            selected, on_done, on_err,
        )

    # ── Dialog helpers ────────────────────────────────────────────────────────

    def _show_ai_response(self, title: str, body: str) -> None:
        win = _make_dialog(self, title, width=620, height=420, resizable=True)

        Frame(win, bg=ACCENT, height=2).pack(side="top", fill="x")

        tb = Text(
            win,
            bg=BG_WINDOW, fg=FG_PRIMARY,
            font=("Consolas", 11),
            wrap="word", relief="flat", bd=0,
            padx=16, pady=14,
            highlightthickness=0,
        )
        tb.pack(fill="both", expand=True)
        tb.insert("1.0", body)
        tb.configure(state="disabled")

        btn_row = Frame(win, bg=BG_SURFACE)
        btn_row.pack(fill="x", padx=16, pady=12)

        def _copy():
            self.clipboard_clear()
            self.clipboard_append(body)

        _make_btn(btn_row, "Close",             win.destroy).pack(side="right")
        _make_btn(btn_row, "Copy to Clipboard", _copy, primary=True).pack(
            side="right", padx=(0, 8)
        )

    def _show_loading_popup(self, message: str) -> Toplevel:
        win = _make_dialog(self, "Please wait…", width=300, height=96)
        Frame(win, bg=ACCENT, height=2).pack(side="top", fill="x")
        Label(
            win, text=message,
            bg=BG_SURFACE, fg=FG_PRIMARY,
            font=("Segoe UI", 10),
        ).pack(expand=True, padx=24, pady=20)
        win.update()
        return win

    def _show_messagebox(self, title: str, message: str) -> None:
        win = _make_dialog(self, title, width=400, height=160)
        win.grab_set()
        Frame(win, bg=ACCENT, height=2).pack(side="top", fill="x")
        Label(
            win, text=message,
            bg=BG_SURFACE, fg=FG_PRIMARY,
            font=("Segoe UI", 9),
            justify="left", wraplength=360,
        ).pack(padx=20, pady=(16, 12), anchor="w")
        _make_btn(win, "OK", win.destroy, primary=True).pack(
            padx=20, pady=(0, 16), anchor="e"
        )
        self.wait_window(win)

    def _confirm_discard_changes(self, name: str) -> bool:
        result: Dict[str, bool] = {"answer": False}

        win = _make_dialog(self, "Unsaved Changes", width=380, height=160)
        win.grab_set()
        Frame(win, bg="#c42b1c", height=2).pack(side="top", fill="x")
        Label(
            win,
            text=f"Discard unsaved changes in '{name}'?",
            bg=BG_SURFACE, fg=FG_PRIMARY,
            font=("Segoe UI", 9), wraplength=340,
        ).pack(padx=20, pady=(16, 12), anchor="w")

        def _set(v: bool):
            result["answer"] = v
            win.destroy()

        br = Frame(win, bg=BG_SURFACE)
        br.pack(padx=20, pady=(0, 16), anchor="e")
        _make_btn(br, "Cancel",  lambda: _set(False)).pack(side="left", padx=(0, 8))
        _make_btn(br, "Discard", lambda: _set(True), danger=True).pack(side="left")

        self.wait_window(win)
        return result["answer"]

    def _rerun_setup(self) -> None:
        """Reset the setup flag and open the wizard immediately."""
        SetupWizard.reset()
        self.withdraw()
        wiz = SetupWizard(self)
        self.wait_window(wiz)
        self.deiconify()

    def show_crisis_resources(self) -> None:
        """Show a scrollable window of mental-health crisis helplines."""
        win = _make_dialog(
            self, "Mental Health Crisis Resources",
            width=560, height=580, resizable=True,
        )
        win.grab_set()

        # ── Accent top bar in red (urgency) ────────────────────────────────
        Frame(win, bg="#c42b1c", height=3).pack(side="top", fill="x")

        # ── Header ─────────────────────────────────────────────────────────
        hdr = Frame(win, bg=BG_SURFACE)
        hdr.pack(fill="x", padx=0, pady=0)
        Label(
            hdr, text="🆘  Mental Health Crisis Resources",
            bg=BG_SURFACE, fg=FG_PRIMARY,
            font=("Segoe UI", 13, "bold"),
        ).pack(pady=(14, 2))
        Label(
            hdr,
            text="If you are in crisis, please reach out. You are not alone.",
            bg=BG_SURFACE, fg=FG_SECONDARY,
            font=("Segoe UI", 9, "italic"),
        ).pack(pady=(0, 10))
        Frame(hdr, bg=BORDER, height=1).pack(fill="x")

        # ── Scrollable body ────────────────────────────────────────────────
        canvas  = tk.Canvas(win, bg=BG_SURFACE, bd=0, highlightthickness=0)
        vscroll = Scrollbar(win, orient="vertical", command=canvas.yview,
                            bg=BG_WINDOW, troughcolor=BG_WINDOW,
                            activebackground=BORDER, relief="flat",
                            width=8, bd=0, highlightthickness=0)
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = Frame(canvas, bg=BG_SURFACE)
        body_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_configure(_e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(body_id, width=canvas.winfo_width())

        body.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_configure)
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        def _section(title: str, colour: str = ACCENT) -> None:
            Frame(body, bg=DIVIDER, height=1).pack(fill="x", padx=16, pady=(12, 0))
            Label(
                body, text=title,
                bg=BG_SURFACE, fg=colour,
                font=("Segoe UI", 10, "bold"), anchor="w",
            ).pack(fill="x", padx=18, pady=(6, 4))

        def _card(name: str, number: str, hours: str = "") -> None:
            card = Frame(body, bg=BG_ELEVATED,
                         highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", padx=18, pady=3)
            Label(
                card, text=name,
                bg=BG_ELEVATED, fg=FG_PRIMARY,
                font=("Segoe UI", 10, "bold"), anchor="w",
            ).pack(fill="x", padx=12, pady=(6, 1))
            detail = f"📞  {number}" + (f"   •   {hours}" if hours else "")
            Label(
                card, text=detail,
                bg=BG_ELEVATED, fg=FG_SECONDARY,
                font=("Segoe UI", 9), anchor="w",
            ).pack(fill="x", padx=12, pady=(0, 6))

        def _bullet(text: str) -> None:
            Label(
                body, text=f"  •  {text}",
                bg=BG_SURFACE, fg=FG_PRIMARY,
                font=("Segoe UI", 9), anchor="w", wraplength=490,
            ).pack(fill="x", padx=18, pady=1)

        # ── India ──────────────────────────────────────────────────────────
        _section("🇮🇳  INDIA  —  24 / 7 Helplines")
        _card("Vandrevala Foundation",     "+91 9999 666 555",   "24/7 · Multilingual")
        _card("Tele-MANAS (Govt.)",        "14416 / 1800-891-4416", "24/7 · Free")
        _card("AASRA",                     "+91 22 2754 6669",   "24/7")
        _card("iCall (TISS)",              "+91 22 2556 3291",   "Mon–Sat 8 am – 10 pm")
        _card("Sneha Foundation (Chennai)","+91 44 2464 0050",   "24/7")
        _card("Sumaitri (Delhi)",          "+91 11 2338 9090",   "2 pm – 10 pm")
        _card("Vandrevala (WhatsApp)",     "+91 9999 666 555",   "WhatsApp available")

        # ── India Emergency ────────────────────────────────────────────────
        _section("🚨  INDIA  —  Emergency Numbers", colour="#f85149")
        _card("Police",            "100")
        _card("Ambulance",         "108")
        _card("Women's Helpline",  "181")
        _card("Disaster Mgmt.",    "108")

        # ── Global ────────────────────────────────────────────────────────
        _section("🌍  GLOBAL RESOURCES")
        _bullet("Befrienders Worldwide (find local line): befrienders.org")
        _bullet("International Assoc. for Suicide Prevention: iasp.info")
        _bullet("Find a Helpline (by country): findahelpline.com")
        _bullet("Crisis Text Line (US/UK/IE/CA): text HOME to 741741")
        _bullet("Samaritans (UK & Ireland): 116 123")

        # ── Closing note ───────────────────────────────────────────────────
        Frame(body, bg=DIVIDER, height=1).pack(fill="x", padx=16, pady=(14, 0))
        Label(
            body,
            text=(
                "These services are free, confidential, and available right now.\n"
                "Reaching out is a sign of strength — not weakness."
            ),
            bg=BG_SURFACE, fg=FG_SECONDARY,
            font=("Segoe UI", 9, "italic"),
            justify="center", wraplength=490,
        ).pack(pady=(10, 16))

        # ── Close button ───────────────────────────────────────────────────
        _make_btn(win, "Close", win.destroy).pack(pady=(0, 16))

        win.update_idletasks()
        _on_configure()

    def show_about(self) -> None:
        """Comprehensive About dialog — features, shortcuts, credits."""
        win = _make_dialog(self, "About Noctis", width=680, height=640, resizable=True)
        win.grab_set()

        # ── Header ─────────────────────────────────────────────────────────
        hdr = Frame(win, bg=BG_WINDOW)
        hdr.pack(fill="x")
        Frame(hdr, bg=ACCENT, height=3).pack(fill="x")
        Label(
            hdr, text="🌙  Noctis",
            bg=BG_WINDOW, fg=FG_PRIMARY,
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(14, 2))
        Label(
            hdr, text="Your Private Mental Health Notepad",
            bg=BG_WINDOW, fg=FG_SECONDARY,
            font=("Segoe UI", 10),
        ).pack()
        Label(
            hdr, text="Version 1.0.0",
            bg=BG_WINDOW, fg=FG_TERTIARY,
            font=("Segoe UI", 8),
        ).pack(pady=(2, 12))
        Frame(hdr, bg=BORDER, height=1).pack(fill="x")

        # ── Scrollable body ────────────────────────────────────────────────
        canvas  = tk.Canvas(win, bg=BG_SURFACE, bd=0, highlightthickness=0)
        vscroll = Scrollbar(win, orient="vertical", command=canvas.yview,
                            bg=BG_WINDOW, troughcolor=BG_WINDOW,
                            activebackground=BORDER, relief="flat",
                            width=8, bd=0, highlightthickness=0)
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = Frame(canvas, bg=BG_SURFACE)
        body_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def _resize(_e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(body_id, width=canvas.winfo_width())

        body.bind("<Configure>", _resize)
        canvas.bind("<Configure>", _resize)
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"),
        )

        PAD = dict(padx=20)

        # ── helpers ───────────────────────────────────────────────────────
        def _h2(text: str) -> None:
            Frame(body, bg=DIVIDER, height=1).pack(fill="x", padx=16, pady=(16, 0))
            Label(
                body, text=text,
                bg=BG_SURFACE, fg=FG_PRIMARY,
                font=("Segoe UI", 12, "bold"), anchor="w",
            ).pack(fill="x", pady=(8, 4), **PAD)

        def _card(icon: str, title: str, desc: str) -> None:
            card = Frame(body, bg=BG_ELEVATED,
                         highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", padx=20, pady=3)
            Label(
                card, text=f"{icon}  {title}",
                bg=BG_ELEVATED, fg=FG_PRIMARY,
                font=("Segoe UI", 10, "bold"), anchor="w",
            ).pack(fill="x", padx=12, pady=(7, 1))
            Label(
                card, text=desc,
                bg=BG_ELEVATED, fg=FG_SECONDARY,
                font=("Segoe UI", 9), anchor="w", wraplength=580,
            ).pack(fill="x", padx=12, pady=(0, 7))

        def _shortcut_row(parent: Frame, key: str, action: str) -> None:
            row = Frame(parent, bg=BG_ELEVATED)
            row.pack(fill="x", padx=4, pady=1)
            Label(
                row, text=key,
                bg=BG_ELEVATED, fg=ACCENT,
                font=("Consolas", 9), width=16, anchor="w",
            ).pack(side="left", padx=(10, 0))
            Label(
                row, text=action,
                bg=BG_ELEVATED, fg=FG_SECONDARY,
                font=("Segoe UI", 9), anchor="w",
            ).pack(side="left", padx=(6, 10), pady=3)

        # ── Privacy banner ─────────────────────────────────────────────────
        banner = Frame(body, bg=BG_ELEVATED,
                       highlightthickness=1, highlightbackground=ACCENT)
        banner.pack(fill="x", padx=20, pady=(16, 4))
        Label(
            banner, text="🔒  100% Local — Zero Data Collection",
            bg=BG_ELEVATED, fg=ACCENT,
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(10, 3))
        Label(
            banner,
            text=(
                "No internet required  •  All notes stay on your device  •"
                "  AI runs completely offline"
            ),
            bg=BG_ELEVATED, fg=FG_SECONDARY,
            font=("Segoe UI", 9), wraplength=580,
        ).pack(pady=(0, 10))

        # ── Features ───────────────────────────────────────────────────────
        _h2("✨  Features")
        for icon, title, desc in [
            ("📝", "Multi-Tab Editor",
             "Work on multiple notes at once with a Chrome-style inline tab bar."),
            ("🤖", "Local AI Companion",
             f"Empathetic AI ({AI_MODEL} via Ollama) running 100 % on your device — "
             "nothing is ever sent to the cloud."),
            ("🔍", "Find & Replace",
             "Full-text search with live highlights and one-click replacement."),
            ("🎨", "Themes & Custom Colors",
             "8 built-in themes (Dark, Light, Gruvbox, Nord, Dracula, Monokai, "
             "Solarized, GitHub Dark) plus a custom colour picker with live preview."),
            ("🖼", "Image Support",
             "Paste images from the clipboard or insert from disk (Ctrl+Shift+I)."),
            ("📊", "Smart Summarize",
             "AI-generated summary of the current note in seconds."),
            ("✍",  "Grammar Fixer",
             "Rewrite selected text with corrected grammar while preserving your tone."),
            ("💾", "Unsaved-change Indicators",
             "📝 icon + green dot on modified tabs; auto-prompt on close."),
            ("🆘", "Crisis Resources",
             "Instant access to India & global mental-health helplines — always offline."),
        ]:
            _card(icon, title, desc)

        # ── Keyboard shortcuts ─────────────────────────────────────────────
        _h2("⌨  Keyboard Shortcuts")

        shortcut_groups = [
            ("File", [
                ("Ctrl+N",         "New Tab"),
                ("Ctrl+O",         "Open File"),
                ("Ctrl+S",         "Save"),
                ("Ctrl+Shift+S",   "Save As"),
                ("Ctrl+W",         "Close Tab"),
            ]),
            ("Editing", [
                ("Ctrl+Z",  "Undo"),
                ("Ctrl+Y",  "Redo"),
                ("Ctrl+X",  "Cut"),
                ("Ctrl+C",  "Copy"),
                ("Ctrl+V",  "Paste"),
                ("Ctrl+A",  "Select All"),
                ("Ctrl+F",  "Find & Replace"),
            ]),
            ("View", [
                ("Ctrl+=",   "Zoom In"),
                ("Ctrl+-",   "Zoom Out"),
                ("Ctrl+0",   "Reset Zoom"),
            ]),
            ("AI", [
                ("Ctrl+`",       "Toggle AI Mode"),
                ("Ctrl+Shift+A", "Toggle AI Mode (alt.)"),
                ("Ctrl+Shift+I", "Insert Image"),
            ]),
        ]

        for category, pairs in shortcut_groups:
            grp = Frame(body, bg=BG_ELEVATED,
                        highlightthickness=1, highlightbackground=BORDER)
            grp.pack(fill="x", padx=20, pady=(4, 2))
            Label(
                grp, text=category,
                bg=BG_ELEVATED, fg=FG_PRIMARY,
                font=("Segoe UI", 9, "bold"), anchor="w",
            ).pack(fill="x", padx=10, pady=(7, 2))
            for key, action in pairs:
                _shortcut_row(grp, key, action)
            Label(grp, text="", bg=BG_ELEVATED, height=1).pack()

        # ── Tech stack ─────────────────────────────────────────────────────
        _h2("🛠  Built With")
        tech = Frame(body, bg=BG_ELEVATED,
                     highlightthickness=1, highlightbackground=BORDER)
        tech.pack(fill="x", padx=20, pady=(0, 4))
        for item in [
            "Python 3.13",
            "Tkinter  (pure — no extra UI framework)",
            f"Ollama  ({AI_MODEL})",
            "Pillow  (image support)",
        ]:
            Label(
                tech, text=f"  •  {item}",
                bg=BG_ELEVATED, fg=FG_SECONDARY,
                font=("Segoe UI", 9), anchor="w",
            ).pack(fill="x", padx=8, pady=2)
        Label(tech, text="", bg=BG_ELEVATED, height=1).pack()

        # ── Credits & GitHub link ──────────────────────────────────────────
        _h2("👤  Developer")
        cred = Frame(body, bg=BG_ELEVATED,
                     highlightthickness=1, highlightbackground=BORDER)
        cred.pack(fill="x", padx=20, pady=(0, 20))
        Label(
            cred, text="Parth Ghumatkar",
            bg=BG_ELEVATED, fg=FG_PRIMARY,
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(10, 3))

        gh_link = Label(
            cred, text="github.com/ParthGhumatkar/noctis",
            bg=BG_ELEVATED, fg=ACCENT,
            font=("Segoe UI", 9, "underline"),
            cursor="hand2",
        )
        gh_link.pack(pady=(0, 10))
        gh_link.bind(
            "<Button-1>",
            lambda _: __import__("webbrowser").open(
                "https://github.com/ParthGhumatkar/noctis"
            ),
        )

        # ── Close button ───────────────────────────────────────────────────
        _make_btn(win, "Close", win.destroy, primary=True).pack(pady=(0, 16))

        win.update_idletasks()
        _resize()

    # ── Status bar ────────────────────────────────────────────────────────────

    def _update_status_from_event(self, _event: object) -> None:
        self._update_status()

    def _update_status(self) -> None:
        tab = self._get_current_tab()
        if not tab:
            return
        index     = tab.text.index("insert")
        line, col = index.split(".")
        col_num   = int(col) + 1
        content   = tab.text.get("1.0", "end-1c")
        words     = len(content.split()) if content.strip() else 0
        self.status_pos_label.config(text=f"Ln {line}, Col {col_num}")
        self.status_words_label.config(
            text=f"{words} word{'s' if words != 1 else ''}"
        )

    def _on_text_modified(self, event: object) -> None:
        widget = event.widget  # type: ignore[union-attr]
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
        # Update title text (no prefix — dot_label handles the unsaved indicator)
        tab.button.config(text=self._truncate(tab.title))
        # Update file icon
        if tab.icon_label is not None:
            tab.icon_label.config(text="📝" if tab.unsaved else "📄")
        # Show/hide the green unsaved dot by changing its fg to match bg or ACCENT
        if tab.dot_label is not None:
            outer_bg = tab.tab_outer.cget("bg") if tab.tab_outer else BG_WINDOW
            tab.dot_label.config(fg=ACCENT if tab.unsaved else outer_bg)

    @staticmethod
    def _truncate(text: str, max_chars: int = 22) -> str:
        return text[: max_chars - 1] + "…" if len(text) > max_chars else text

    # ── Theme system ──────────────────────────────────────────────────────────

    def _themes_items(self) -> List[Dict]:
        """Dynamic Themes menu — shows ✓ next to the active theme."""
        items: List[Dict] = []
        for name in THEMES:
            icon = "✓" if name == self.current_theme else "  "
            items.append({
                "type": "command", "icon": icon,
                "label": name, "shortcut": "",
                "command": lambda n=name: self.apply_theme(n),
            })
        items.append({"type": "separator"})
        items.append({
            "type": "command", "icon": "🎨",
            "label": "Custom Colors…", "shortcut": "",
            "command": self.open_custom_colors,
        })
        return items

    def apply_theme(self, theme_name: str) -> None:
        """Apply a named theme to every widget in the app."""
        if theme_name not in THEMES:
            return
        t = THEMES[theme_name]

        # Validate custom (user-built) themes before applying; presets are safe
        # by construction so we skip their check to avoid false positives.
        _BUILTIN = frozenset(THEMES.keys()) - {"Custom"}
        if theme_name not in _BUILTIN:
            ok, msg = validate_theme(t)
            if not ok:
                self._show_messagebox(
                    "Invalid Theme",
                    f"Cannot apply this custom theme:\n\n{msg}\n\n"
                    "Please adjust the colours and try again.",
                )
                return   # leave the current theme intact

        self.current_theme = theme_name
        self.theme_var.set(theme_name)

        # ── Update module-level globals so new widgets pick up the right colours
        g = globals()
        for key in (
            "BG_WINDOW", "BG_SURFACE", "BG_ELEVATED",
            "FG_PRIMARY", "FG_SECONDARY", "FG_TERTIARY",
            "ACCENT", "ACCENT_HOVER", "ACCENT_DARK", "ACCENT_SUBTLE",
            "BORDER", "DIVIDER", "SELECT_BG", "CURSOR_CLR",
            "DROPDOWN_BG", "MENU_ITEM_HOVER",
        ):
            g[key] = t[key]
        g["EDITOR_BG"] = g["WIN_BG"] = g["MENU_BG"] = t["BG_WINDOW"]
        g["EDITOR_FG"] = g["FG"]     = t["FG_PRIMARY"]
        g["FG_DIM"]                  = t["FG_SECONDARY"]
        g["HOVER_BG"]                = t["BG_ELEVATED"]

        BW  = t["BG_WINDOW"];   BS  = t["BG_SURFACE"];   BE  = t["BG_ELEVATED"]
        FP  = t["FG_PRIMARY"];  FS  = t["FG_SECONDARY"]; FT  = t["FG_TERTIARY"]
        AC  = t["ACCENT"];      AH  = t["ACCENT_HOVER"]
        AD  = t["ACCENT_DARK"]; ASU = t["ACCENT_SUBTLE"]
        DI  = t["DIVIDER"];     BO  = t["BORDER"]
        SEL = t["SELECT_BG"];   CUR = t["CURSOR_CLR"]

        # ── Main window ─────────────────────────────────────────────────────
        self.configure(bg=BW)
        self.tk_setPalette(background=BW, foreground=FP)

        # ── Menu bar ────────────────────────────────────────────────────────
        self.menubar_frame.config(bg=BS)
        for btn in self._menu_buttons.values():
            btn.config(bg=BS, fg=FS,
                       activebackground=BE, activeforeground=FP)

        # ── Dividers ────────────────────────────────────────────────────────
        for div in self._dividers:
            div.config(bg=DI)

        # ── Tab bar ─────────────────────────────────────────────────────────
        self.tabs_bar.config(bg=BW)
        self.tabs_container.config(bg=BW)

        # AI button
        if self._ai_mode:
            self.ai_toggle_btn.config(
                bg=AC, fg=BW, activebackground=AH,
                highlightbackground=AH,
            )
        else:
            self.ai_toggle_btn.config(
                bg=AD, fg="#ffffff", activebackground=ASU,
                highlightbackground=AD,
            )

        # New-tab + button
        self.new_tab_button.config(
            bg=BW, fg=AC, activebackground=BE, activeforeground=AH,
        )

        # ── Status bar ──────────────────────────────────────────────────────
        self.statusbar.config(bg=BW)
        self.status_pos_label.config(bg=BW, fg=FS)
        self.status_words_label.config(bg=BW, fg=FS)
        self.status_ai_label.config(bg=BW)
        for lbl in self._status_sep_labels:
            lbl.config(bg=BW, fg=FT)
        for lbl in self._status_static_labels:
            lbl.config(bg=BW, fg=FS)

        # ── Editor container ────────────────────────────────────────────────
        self.editor_container.config(bg=BW)

        # ── Individual tabs ─────────────────────────────────────────────────
        for i, tab in enumerate(self.tabs):
            is_active = (i == self.current_tab_index)
            tab_bg    = BE if is_active else BW

            tab.text.config(
                bg=BW, fg=FP,
                insertbackground=CUR,
                selectbackground=SEL,
                selectforeground=FP,
            )
            tab.frame.config(bg=BW)
            if tab.scrollbar is not None:
                tab.scrollbar.config(
                    bg=BW, troughcolor=BW, activebackground=BO,
                )

            for w in (tab.tab_outer, tab.tab_inner, tab.icon_label):
                if w is not None:
                    w.config(bg=tab_bg)
            if tab.dot_label is not None:
                dot_fg = AC if tab.unsaved else tab_bg
                tab.dot_label.config(bg=tab_bg, fg=dot_fg)

            tab.button.config(bg=tab_bg, fg=FP if is_active else FS)
            tab.indicator.config(bg=AC if is_active else BW)
            tab.close_button.config(
                bg=tab_bg, fg=FS if is_active else tab_bg,
            )

        # Also re-tag AI content so it uses the new accent colour
        cur_tab = self._get_current_tab()
        if cur_tab:
            self._ensure_ai_tags(cur_tab.text)

        self._save_theme_preference()

    def _save_theme_preference(self) -> None:
        config_dir  = Path.home() / ".noctis"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.json"
        try:
            config_file.write_text(
                json.dumps({"theme": self.current_theme}, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _load_theme_preference(self) -> None:
        config_file = Path.home() / ".noctis" / "config.json"
        if not config_file.exists():
            return
        try:
            cfg   = json.loads(config_file.read_text(encoding="utf-8"))
            theme = cfg.get("theme", "Dark (Default)")
            if theme in THEMES:
                self.apply_theme(theme)
        except Exception:
            pass

    def open_custom_colors(self) -> None:
        """Custom color picker dialog with live validation + editor preview."""
        base = THEMES.get(self.current_theme, THEMES["Dark (Default)"])

        fields = [
            ("Window / Editor BG", "BG_WINDOW"),
            ("Surface (menus)",    "BG_SURFACE"),
            ("Active / Hover BG",  "BG_ELEVATED"),
            ("Primary Text",       "FG_PRIMARY"),
            ("Secondary Text",     "FG_SECONDARY"),
            ("Accent Colour",      "ACCENT"),
        ]

        win = _make_dialog(self, "Custom Colors", width=530, height=520, resizable=False)
        win.grab_set()
        Frame(win, bg=ACCENT, height=2).pack(side="top", fill="x")

        Label(
            win, text="Custom Theme Colors",
            bg=BG_SURFACE, fg=FG_PRIMARY,
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(10, 2))
        Label(
            win, text="Adjust colors then click Apply. Invalid combos are blocked.",
            bg=BG_SURFACE, fg=FG_SECONDARY,
            font=("Segoe UI", 8),
        ).pack(pady=(0, 8))

        # ── Color fields ────────────────────────────────────────────────────
        grid = Frame(win, bg=BG_SURFACE)
        grid.pack(fill="x", padx=20)

        vars_: Dict[str, StringVar] = {}
        swatch_btns: Dict[str, Button] = {}

        for row, (lbl_text, key) in enumerate(fields):
            Label(
                grid, text=lbl_text,
                bg=BG_SURFACE, fg=FG_PRIMARY,
                font=("Segoe UI", 9), anchor="w", width=20,
            ).grid(row=row, column=0, padx=(0, 6), pady=3, sticky="w")

            sv = StringVar(value=base.get(key, "#000000"))
            vars_[key] = sv

            ent = _make_entry(grid, width=9, textvariable=sv)
            ent.grid(row=row, column=1, padx=(0, 6), pady=3)

            swatch = Button(
                grid, text="   ", relief="flat", cursor="hand2",
                bg=base.get(key, "#000000"), bd=1,
                highlightbackground=BORDER,
            )
            swatch.grid(row=row, column=2, padx=(0, 6), pady=3)
            swatch_btns[key] = swatch

            def _pick(k=key, s=sv, sw=swatch):
                rgb, hx = colorchooser.askcolor(
                    color=s.get(), parent=win,
                    title=f"Choose {dict(fields)[k]}",
                )
                if hx:
                    s.set(hx)
                    sw.config(bg=hx)

            swatch.config(command=_pick)

        # ── Editor preview ───────────────────────────────────────────────────
        Frame(win, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(10, 0))
        Label(
            win, text="PREVIEW",
            bg=BG_SURFACE, fg=FG_TERTIARY,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=22, pady=(4, 2))

        preview_text = Text(
            win,
            height=4,
            bg=base.get("BG_WINDOW", BG_WINDOW),
            fg=base.get("FG_PRIMARY", FG_PRIMARY),
            insertbackground=base.get("ACCENT", ACCENT),
            font=("Consolas", 10),
            relief="flat", bd=0,
            padx=12, pady=8,
            state="disabled",
        )
        preview_text.pack(fill="x", padx=20, pady=(0, 4))
        _preview_content = (
            "This is how your editor will look.\n"
            "The quick brown fox jumps over the lazy dog.\n"
            ">>> AI prompt example | Ln 1, Col 1"
        )
        preview_text.config(state="normal")
        preview_text.insert("1.0", _preview_content)
        preview_text.config(state="disabled")

        # ── Validation status label ──────────────────────────────────────────
        Frame(win, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(2, 0))
        status_lbl = Label(
            win, text="",
            bg=BG_SURFACE, fg=FG_SECONDARY,
            font=("Segoe UI", 9),
            anchor="w", wraplength=480,
        )
        status_lbl.pack(fill="x", padx=22, pady=(4, 2))

        # ── Live update logic ────────────────────────────────────────────────

        def _build_custom() -> Dict[str, str]:
            """Assemble the full custom theme dict from the current StringVars."""
            c: Dict[str, str] = dict(base)
            for k, sv in vars_.items():
                val = sv.get().strip()
                if len(val) == 7 and val.startswith("#"):
                    c[k] = val
            c["CURSOR_CLR"]      = c["ACCENT"]
            c["ACCENT_HOVER"]    = c["ACCENT"]
            c["ACCENT_DARK"]     = c["ACCENT"]
            c["ACCENT_SUBTLE"]   = c["ACCENT"]
            c["DROPDOWN_BG"]     = c["BG_ELEVATED"]
            c["MENU_ITEM_HOVER"] = c["BG_ELEVATED"]
            c["DIVIDER"]         = c["BG_SURFACE"]
            c["BORDER"]          = c["BG_ELEVATED"]
            c["SELECT_BG"]       = c["BG_ELEVATED"]
            c["FG_TERTIARY"]     = c["FG_SECONDARY"]
            return c

        def _refresh(*_) -> None:
            """Called on every color change — update swatch, preview, validation."""
            c = _build_custom()

            # Update swatches for any valid hex values
            for k, sw in swatch_btns.items():
                v = vars_[k].get().strip()
                if len(v) == 7 and v.startswith("#"):
                    try:
                        sw.config(bg=v)
                    except Exception:
                        pass

            # Update editor preview colours
            bw = c.get("BG_WINDOW", "")
            fp = c.get("FG_PRIMARY", "")
            if len(bw) == 7 and bw.startswith("#"):
                try:
                    preview_text.config(bg=bw)
                except Exception:
                    pass
            if len(fp) == 7 and fp.startswith("#"):
                try:
                    preview_text.config(fg=fp)
                except Exception:
                    pass

            # Validate and update status + Apply button
            ok, msg = validate_theme(c)
            if ok:
                status_lbl.config(
                    text="✓  Theme looks good — contrast and colour rules pass.",
                    fg="#3fb950",  # green regardless of theme
                )
                apply_btn.config(state="normal")
            else:
                status_lbl.config(text=f"⚠  {msg}", fg="#f85149")  # red
                apply_btn.config(state="disabled")

        def _reset() -> None:
            default = THEMES["Dark (Default)"]
            for k, sv in vars_.items():
                sv.set(default.get(k, "#000000"))
                swatch_btns[k].config(bg=default.get(k, "#000000"))
            _refresh()

        def _do_apply() -> None:
            c = _build_custom()
            ok, msg = validate_theme(c)
            if not ok:
                return
            THEMES["Custom"] = c
            win.destroy()
            self.apply_theme("Custom")

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_row = Frame(win, bg=BG_SURFACE)
        btn_row.pack(fill="x", padx=20, pady=(4, 14))

        apply_btn = _make_btn(btn_row, "Apply", _do_apply, primary=True)
        apply_btn.pack(side="right")
        _make_btn(btn_row, "Cancel", win.destroy).pack(side="right", padx=(0, 8))
        _make_btn(btn_row, "Reset to Default", _reset).pack(side="left")

        # Wire every StringVar to _refresh
        for sv in vars_.values():
            sv.trace_add("write", _refresh)

        _refresh()   # set initial status

    # ── AI toggle helpers ─────────────────────────────────────────────────────

    def _toggle_ai_with_flash(self) -> None:
        """Toggle AI and briefly flash the button as visual feedback."""
        self.toggle_ai()
        btn = self.ai_toggle_btn
        flash_bg = ACCENT_HOVER if self._ai_mode else ACCENT_SUBTLE
        orig_bg  = btn.cget("bg")
        btn.config(bg=flash_bg)
        self.after(140, lambda: btn.config(bg=orig_bg))

    # ── Keybindings & exit ────────────────────────────────────────────────────

    def _create_keybindings(self) -> None:
        b = self.bind
        b("<Control-n>",       lambda _: self.new_tab())
        b("<Control-N>",       lambda _: self.new_tab())
        b("<Control-o>",       lambda _: self.open_file())
        b("<Control-O>",       lambda _: self.open_file())
        b("<Control-s>",       lambda _: self.save_file())
        b("<Control-S>",       lambda _: self.save_file())
        b("<Control-Shift-S>", lambda _: self.save_file_as())
        b("<Control-w>",       lambda _: self.close_tab())
        b("<Control-W>",       lambda _: self.close_tab())
        b("<Control-z>",       lambda _: self._editor_undo())
        b("<Control-Z>",       lambda _: self._editor_undo())
        b("<Control-y>",       lambda _: self._editor_redo())
        b("<Control-Y>",       lambda _: self._editor_redo())
        b("<Control-f>",       lambda _: self.open_find_replace())
        b("<Control-F>",       lambda _: self.open_find_replace())
        b("<Control-a>",       lambda _: self._editor_select_all())
        b("<Control-A>",       lambda _: self._editor_select_all())
        b("<Control-Shift-I>", lambda _: self.insert_image())
        b("<Control-equal>",   lambda _: self._zoom_in())
        b("<Control-minus>",   lambda _: self._zoom_out())
        b("<Control-0>",       lambda _: self._zoom_reset())
        # AI mode toggle shortcuts
        b("<Control-grave>",   lambda _: self._toggle_ai_with_flash())   # Ctrl+`
        b("<Control-Shift-A>", lambda _: self._toggle_ai_with_flash())   # Ctrl+Shift+A
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def on_exit(self) -> None:
        for tab in list(self.tabs):
            if tab.unsaved and not self._confirm_discard_changes(tab.title):
                return
        self.destroy()


if __name__ == "__main__":
    app = Noctis()
    app.mainloop()
