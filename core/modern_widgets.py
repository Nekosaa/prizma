"""Modern widgets for Prizma Studio.

Contains:
    * BrowserTabBar   — browser-style tabs per opened file with close (×) button
    * ModernSidebar   — 240 px left rail with brand + recent files list
    * WelcomeScreen   — centred greeting when no file is open
    * ModernLogPanel  — collapsible log with coloured level icons
"""
from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Optional

from core.i18n import i18n
from core.theme_modern import get_palette


# ---------------------------------------------------------------------------
# BrowserTabBar
# ---------------------------------------------------------------------------
class BrowserTabBar(ttk.Frame):
    """Horizontal browser-style tabs.

    Each tab shows an icon + filename + close (×) button. Clicking a tab
    switches the active tab; clicking × closes it. The caller supplies:
        on_activate(tab_id)  – called when a tab becomes active
        on_close(tab_id)     – called when its × button is pressed
    """

    def __init__(
        self,
        master: tk.Misc,
        on_activate: Callable[[str], None],
        on_close: Callable[[str], None],
    ) -> None:
        super().__init__(master, style="TabBar.TFrame", padding=(8, 6, 8, 0))
        self._on_activate = on_activate
        self._on_close = on_close
        self._tabs: dict[str, dict] = {}       # tab_id -> {frame, label, close, kind, title}
        self._order: list[str] = []
        self._active: Optional[str] = None

        self._container = ttk.Frame(self, style="TabBar.TFrame")
        self._container.pack(side="left", fill="x", expand=True)

    # -- public API --------------------------------------------------------
    def add_tab(self, tab_id: str, title: str, kind: str = "pdf") -> None:
        """Create a new tab. ``kind`` is 'pdf' | 'psd' | 'settings' | 'about'."""
        if tab_id in self._tabs:
            self.set_active(tab_id)
            return

        icon = {"pdf": "📄", "psd": "🎨", "settings": "⚙", "about": "ℹ"}.get(kind, "•")

        wrap = ttk.Frame(self._container, style="Tab.TFrame", padding=(10, 6, 6, 6))
        wrap.pack(side="left", padx=(0, 4))

        title_lbl = ttk.Label(
            wrap,
            text=f"{icon}  {title}",
            style="Tab.TLabel",
            cursor="hand2",
        )
        title_lbl.pack(side="left")

        close_lbl = ttk.Label(
            wrap, text=" ×", style="TabClose.TLabel", cursor="hand2",
        )
        close_lbl.pack(side="left", padx=(6, 0))

        title_lbl.bind("<Button-1>", lambda _e, tid=tab_id: self._on_activate(tid))
        wrap.bind("<Button-1>", lambda _e, tid=tab_id: self._on_activate(tid))
        close_lbl.bind("<Button-1>", lambda _e, tid=tab_id: self._on_close(tid))

        self._tabs[tab_id] = {
            "frame": wrap,
            "label": title_lbl,
            "close": close_lbl,
            "kind": kind,
            "title": title,
            "icon": icon,
        }
        self._order.append(tab_id)
        self.set_active(tab_id)

    def remove_tab(self, tab_id: str) -> None:
        info = self._tabs.pop(tab_id, None)
        if not info:
            return
        info["frame"].destroy()
        if tab_id in self._order:
            self._order.remove(tab_id)
        if self._active == tab_id:
            self._active = None
            if self._order:
                self.set_active(self._order[-1])

    def set_active(self, tab_id: str) -> None:
        if tab_id not in self._tabs:
            return
        self._active = tab_id
        for tid, info in self._tabs.items():
            if tid == tab_id:
                info["frame"].configure(style="TabActive.TFrame")
                info["label"].configure(style="TabActive.TLabel")
                info["close"].configure(style="TabCloseActive.TLabel")
            else:
                info["frame"].configure(style="Tab.TFrame")
                info["label"].configure(style="Tab.TLabel")
                info["close"].configure(style="TabClose.TLabel")

    def rename_tab(self, tab_id: str, title: str) -> None:
        info = self._tabs.get(tab_id)
        if not info:
            return
        info["title"] = title
        info["label"].configure(text=f"{info['icon']}  {title}")

    def active_id(self) -> Optional[str]:
        return self._active

    def has_tab(self, tab_id: str) -> bool:
        return tab_id in self._tabs

    def tabs(self) -> list[str]:
        return list(self._order)


# ---------------------------------------------------------------------------
# ModernSidebar
# ---------------------------------------------------------------------------
class ModernSidebar(ttk.Frame):
    """240 px sidebar with brand block and recent files list."""

    WIDTH = 240

    def __init__(
        self,
        master: tk.Misc,
        app_name: str,
        on_open_recent: Callable[[str], None],
        on_clear_recent: Callable[[], None],
    ) -> None:
        super().__init__(master, style="Sidebar.TFrame", padding=(16, 18))
        self.configure(width=self.WIDTH)
        self.pack_propagate(False)

        self._on_open_recent = on_open_recent
        self._on_clear_recent = on_clear_recent

        # Brand ---------------------------------------------------------------
        self._brand = ttk.Label(
            self, text=f"◆  {app_name}", style="SidebarBrand.TLabel",
        )
        self._brand.pack(anchor="w")

        self._tagline = ttk.Label(
            self, text=i18n.t("app.tagline"), style="SidebarMuted.TLabel",
        )
        self._tagline.pack(anchor="w", pady=(2, 18))

        # Separator ----------------------------------------------------------
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(0, 12))

        # Recent files section -----------------------------------------------
        self._recent_header = ttk.Label(
            self, text=i18n.t("sidebar.recent"), style="SidebarHeader.TLabel",
        )
        self._recent_header.pack(anchor="w", pady=(0, 6))

        self._recent_container = ttk.Frame(self, style="Sidebar.TFrame")
        self._recent_container.pack(fill="both", expand=True)

        # Clear recent button (bottom) ---------------------------------------
        self._clear_btn = ttk.Button(
            self,
            text=i18n.t("sidebar.clear_recent"),
            style="Sidebar.TButton",
            command=self._on_clear_recent,
        )
        self._clear_btn.pack(fill="x", pady=(10, 0))

        self._items: list[ttk.Label] = []
        i18n.subscribe(self._retranslate)

    # -- public API --------------------------------------------------------
    def set_recent(self, paths: list[str]) -> None:
        for w in self._items:
            w.destroy()
        self._items.clear()

        if not paths:
            empty = ttk.Label(
                self._recent_container,
                text=i18n.t("sidebar.no_recent"),
                style="SidebarMuted.TLabel",
                wraplength=self.WIDTH - 40,
            )
            empty.pack(anchor="w", pady=2)
            self._items.append(empty)
            return

        for path in paths:
            name = Path(path).name or path
            item = ttk.Label(
                self._recent_container,
                text=f"• {name}",
                style="Sidebar.TLabel",
                cursor="hand2",
                wraplength=self.WIDTH - 40,
            )
            item.pack(anchor="w", pady=2)
            item.bind("<Button-1>", lambda _e, p=path: self._on_open_recent(p))
            # Hover feedback (colour swap on active palette).
            palette = get_palette()

            def _enter(_e, w=item, c=palette["accent"]):
                w.configure(foreground=c)

            def _leave(_e, w=item, c=palette["text"]):
                w.configure(foreground=c)

            item.bind("<Enter>", _enter)
            item.bind("<Leave>", _leave)
            self._items.append(item)

    def _retranslate(self) -> None:
        self._tagline.configure(text=i18n.t("app.tagline"))
        self._recent_header.configure(text=i18n.t("sidebar.recent"))
        self._clear_btn.configure(text=i18n.t("sidebar.clear_recent"))


# ---------------------------------------------------------------------------
# WelcomeScreen
# ---------------------------------------------------------------------------
class WelcomeScreen(ttk.Frame):
    """Centred landing screen when no file is open."""

    def __init__(
        self,
        master: tk.Misc,
        app_name: str,
        on_open_pdf: Callable[[], None],
        on_open_psd: Callable[[], None],
    ) -> None:
        super().__init__(master, style="Welcome.TFrame")
        self._on_open_pdf = on_open_pdf
        self._on_open_psd = on_open_psd

        # A vertically centred inner box.
        inner = ttk.Frame(self, style="Welcome.TFrame")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        self._title = ttk.Label(
            inner, text=f"◆  {app_name}", style="WelcomeTitle.TLabel",
        )
        self._title.pack(pady=(0, 4))

        self._tagline = ttk.Label(
            inner, text=i18n.t("app.tagline"), style="WelcomeTagline.TLabel",
        )
        self._tagline.pack(pady=(0, 32))

        btn_row = ttk.Frame(inner, style="Welcome.TFrame")
        btn_row.pack()

        self._pdf_btn = ttk.Button(
            btn_row,
            text=f"📄  {i18n.t('welcome.open_pdf')}",
            style="Accent.TButton",
            command=on_open_pdf,
        )
        self._pdf_btn.pack(side="left", padx=(0, 12))

        self._psd_btn = ttk.Button(
            btn_row,
            text=f"🎨  {i18n.t('welcome.open_psd')}",
            style="Accent.TButton",
            command=on_open_psd,
        )
        self._psd_btn.pack(side="left")

        self._hint = ttk.Label(
            inner, text=i18n.t("welcome.drop_hint"), style="WelcomeHint.TLabel",
        )
        self._hint.pack(pady=(28, 0))

        i18n.subscribe(self._retranslate)

    def _retranslate(self) -> None:
        self._tagline.configure(text=i18n.t("app.tagline"))
        self._pdf_btn.configure(text=f"📄  {i18n.t('welcome.open_pdf')}")
        self._psd_btn.configure(text=f"🎨  {i18n.t('welcome.open_psd')}")
        self._hint.configure(text=i18n.t("welcome.drop_hint"))


# ---------------------------------------------------------------------------
# ModernLogPanel
# ---------------------------------------------------------------------------
class ModernLogPanel(ttk.Frame):
    """Log panel with coloured level indicators."""

    _ICONS = {
        "info":  ("ℹ", "info"),
        "ok":    ("✓", "success"),
        "warn":  ("⚠", "warning"),
        "error": ("✕", "danger"),
    }

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, style="Log.TFrame", padding=(12, 8))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="Log.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        self._title_lbl = ttk.Label(
            header, text=f"📋  {i18n.t('log.title')}", style="LogTitle.TLabel",
        )
        self._title_lbl.grid(row=0, column=0, sticky="w")

        self._clear_btn = ttk.Button(
            header, text=i18n.t("log.clear"), style="Ghost.TButton",
            command=self.clear,
        )
        self._clear_btn.grid(row=0, column=1, sticky="e")

        palette = get_palette()

        self._text = tk.Text(
            self, height=6, wrap="word", relief="flat", borderwidth=0,
            background=palette["log_bg"],
            foreground=palette["text"],
            insertbackground=palette["text"],
            font=("Consolas", 10),
        )
        self._text.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self._text.configure(state="disabled")

        scroll = ttk.Scrollbar(self, orient="vertical", command=self._text.yview)
        scroll.grid(row=1, column=1, sticky="ns", pady=(6, 0))
        self._text.configure(yscrollcommand=scroll.set)

        self._text.tag_configure("info",    foreground=palette["text_muted"])
        self._text.tag_configure("success", foreground=palette["success"])
        self._text.tag_configure("warning", foreground=palette["warning"])
        self._text.tag_configure("danger",  foreground=palette["danger"])

        i18n.subscribe(self._retranslate)

    def _retranslate(self) -> None:
        self._title_lbl.configure(text=f"📋  {i18n.t('log.title')}")
        self._clear_btn.configure(text=i18n.t("log.clear"))

    def log(self, message: str, level: str = "info") -> None:
        icon, tag = self._ICONS.get(level, ("•", "info"))
        self._text.configure(state="normal")
        self._text.insert("end", f"{icon} {message}\n", tag)
        self._text.see("end")
        self._text.configure(state="disabled")

    def clear(self) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")

    def apply_palette(self) -> None:
        """Re-apply text/tag colours after a theme switch."""
        palette = get_palette()
        self._text.configure(
            background=palette["log_bg"],
            foreground=palette["text"],
            insertbackground=palette["text"],
        )
        self._text.tag_configure("info",    foreground=palette["text_muted"])
        self._text.tag_configure("success", foreground=palette["success"])
        self._text.tag_configure("warning", foreground=palette["warning"])
        self._text.tag_configure("danger",  foreground=palette["danger"])
