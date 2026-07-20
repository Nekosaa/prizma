"""Prizma Studio – Modern UI entry point.

Layout (from the user's design brief):

    ┌──────────────────────────────────────────────────────────────────────┐
    │ Top bar:  [PDF] [PSD]    [Settings] [About]   [Lang ▼]                │
    ├──────────┬───────────────────────────────────────────────────────────┤
    │          │  [📄 file1 ×] [🎨 file2 ×] [📄 file3 ×]                    │
    │ Sidebar  ├───────────────────────────────────────────────────────────┤
    │  Brand   │                                                            │
    │  Recent  │                Active content (PDF / PSD / Welcome)        │
    │          │                                                            │
    │          ├───────────────────────────────────────────────────────────┤
    │          │  📋 Log                                        [Clear]     │
    ├──────────┴───────────────────────────────────────────────────────────┤
    │ Status bar                                                            │
    └──────────────────────────────────────────────────────────────────────┘

Every open file gets its own PdfToolsFrame / PsdToolsFrame instance, so
users can jump between multiple PDFs and PSDs like browser tabs.
"""
from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Callable, Optional

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from core import __app_name__, __author__, __version__
from core.config import config
from core.i18n import i18n
from core.modern_widgets import (
    BrowserTabBar,
    ModernLogPanel,
    ModernSidebar,
    WelcomeScreen,
)
from core.theme_modern import apply_modern_theme, get_palette
from modules.pdf_tools_tab import PdfToolsFrame
from modules.psd_tools_tab import PsdToolsFrame

ASSETS_DIR = _HERE / "assets"
MAX_RECENT = 8


# ---------------------------------------------------------------------------
# Settings screen
# ---------------------------------------------------------------------------
class SettingsFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, on_theme_change: Callable[[str], None]) -> None:
        super().__init__(master, padding=24)
        self._on_theme_change = on_theme_change

        self._lang_var = tk.StringVar(value=config.get("language"))
        self._theme_var = tk.StringVar(value=config.get("theme"))
        self._depth_var = tk.IntVar(value=int(config.get("smart_object_depth", 3)))
        self._pdf_dir_var = tk.StringVar(value=config.get("pdf_last_dir"))
        self._psd_in_var = tk.StringVar(value=config.get("psd_in_dir"))
        self._psd_out_var = tk.StringVar(value=config.get("psd_out_dir"))

        self._build()
        i18n.subscribe(self._retranslate)

    def _build(self) -> None:
        for col in range(3):
            self.columnconfigure(col, weight=(1 if col == 1 else 0))

        self._lbl_lang = ttk.Label(self, text=i18n.t("settings.language"),
                                   font=("Segoe UI", 10, "bold"))
        self._lbl_lang.grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._lang_combo = ttk.Combobox(self, textvariable=self._lang_var,
                                        values=["ru", "en"], state="readonly", width=12)
        self._lang_combo.grid(row=0, column=1, sticky="w", pady=(0, 4))
        self._lang_combo.bind("<<ComboboxSelected>>", lambda _e: self._apply_lang())

        self._lbl_hint = ttk.Label(self, text=i18n.t("settings.restart"))
        self._lbl_hint.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 16))

        self._lbl_theme = ttk.Label(self, text=i18n.t("settings.theme"),
                                    font=("Segoe UI", 10, "bold"))
        self._lbl_theme.grid(row=2, column=0, sticky="w", pady=(0, 4))
        self._theme_combo = ttk.Combobox(self, textvariable=self._theme_var,
                                         values=["system", "light", "dark"],
                                         state="readonly", width=12)
        self._theme_combo.grid(row=2, column=1, sticky="w", pady=(0, 4))
        self._theme_combo.bind("<<ComboboxSelected>>", lambda _e: self._apply_theme())

        self._lbl_paths = ttk.Label(self, text=i18n.t("settings.paths"),
                                    font=("Segoe UI", 10, "bold"))
        self._lbl_paths.grid(row=3, column=0, sticky="w", pady=(16, 4))

        self._row_path("settings.pdf_dir", self._pdf_dir_var, 4, "pdf_last_dir")
        self._row_path("settings.psd_in",  self._psd_in_var,  5, "psd_in_dir")
        self._row_path("settings.psd_out", self._psd_out_var, 6, "psd_out_dir")

        self._lbl_depth = ttk.Label(self, text=i18n.t("settings.depth"),
                                    font=("Segoe UI", 10, "bold"))
        self._lbl_depth.grid(row=7, column=0, sticky="w", pady=(16, 4))
        depth_spin = ttk.Spinbox(self, from_=1, to=10, textvariable=self._depth_var,
                                 width=5, command=self._apply_depth)
        depth_spin.grid(row=7, column=1, sticky="w", pady=(16, 4))
        self._depth_var.trace_add("write", lambda *_: self._apply_depth())

    def _row_path(self, key: str, var: tk.StringVar, row: int, cfg_key: str) -> None:
        lbl = ttk.Label(self, text=i18n.t(key))
        lbl.grid(row=row, column=0, sticky="w", padx=(0, 12), pady=2)
        entry = ttk.Entry(self, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", pady=2)
        btn = ttk.Button(self, text=i18n.t("common.browse"),
                         command=lambda: self._pick_dir(var, cfg_key))
        btn.grid(row=row, column=2, sticky="w", padx=(8, 0), pady=2)
        var.trace_add("write", lambda *_: config.set(cfg_key, var.get()))
        setattr(self, f"_lbl_{cfg_key}", lbl)
        setattr(self, f"_btn_{cfg_key}", btn)

    def _pick_dir(self, var: tk.StringVar, cfg_key: str) -> None:
        chosen = filedialog.askdirectory(initialdir=var.get() or str(Path.home()))
        if chosen:
            var.set(chosen)
            config.set(cfg_key, chosen)

    def _apply_lang(self) -> None:
        lang = self._lang_var.get()
        config.set("language", lang)
        i18n.set_language(lang)

    def _apply_theme(self) -> None:
        mode = self._theme_var.get()
        config.set("theme", mode)
        self._on_theme_change(mode)

    def _apply_depth(self) -> None:
        try:
            config.set("smart_object_depth", int(self._depth_var.get()))
        except (tk.TclError, ValueError):
            pass

    def _retranslate(self) -> None:
        self._lbl_lang.configure(text=i18n.t("settings.language"))
        self._lbl_theme.configure(text=i18n.t("settings.theme"))
        self._lbl_paths.configure(text=i18n.t("settings.paths"))
        self._lbl_depth.configure(text=i18n.t("settings.depth"))
        self._lbl_hint.configure(text=i18n.t("settings.restart"))
        self._lbl_pdf_last_dir.configure(text=i18n.t("settings.pdf_dir"))
        self._lbl_psd_in_dir.configure(text=i18n.t("settings.psd_in"))
        self._lbl_psd_out_dir.configure(text=i18n.t("settings.psd_out"))
        for cfg_key in ("pdf_last_dir", "psd_in_dir", "psd_out_dir"):
            getattr(self, f"_btn_{cfg_key}").configure(text=i18n.t("common.browse"))


# ---------------------------------------------------------------------------
# About screen
# ---------------------------------------------------------------------------
class AboutFrame(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=32)
        self.columnconfigure(0, weight=1)

        self._title = ttk.Label(self, text=__app_name__,
                                font=("Segoe UI", 22, "bold"))
        self._title.grid(row=0, column=0, sticky="w")

        self._tagline = ttk.Label(self, text=i18n.t("app.tagline"),
                                  font=("Segoe UI", 11))
        self._tagline.grid(row=1, column=0, sticky="w", pady=(2, 20))

        self._version_lbl = ttk.Label(
            self, text=f"{i18n.t('about.version')}: {__version__}",
            font=("Segoe UI", 10),
        )
        self._version_lbl.grid(row=2, column=0, sticky="w", pady=2)

        self._author_lbl = ttk.Label(
            self, text=f"{i18n.t('about.author')}: {__author__}",
            font=("Segoe UI", 10),
        )
        self._author_lbl.grid(row=3, column=0, sticky="w", pady=2)

        self._desc = ttk.Label(self, text=i18n.t("about.description"),
                               justify="left", wraplength=640)
        self._desc.grid(row=4, column=0, sticky="w", pady=(20, 10))

        self._tech_lbl = ttk.Label(
            self,
            text=f"{i18n.t('about.tech')}: Python · Tkinter · sv-ttk · PyMuPDF · Pillow · pywin32",
        )
        self._tech_lbl.grid(row=5, column=0, sticky="w", pady=(20, 0))

        i18n.subscribe(self._retranslate)

    def _retranslate(self) -> None:
        self._tagline.configure(text=i18n.t("app.tagline"))
        self._version_lbl.configure(text=f"{i18n.t('about.version')}: {__version__}")
        self._author_lbl.configure(text=f"{i18n.t('about.author')}: {__author__}")
        self._desc.configure(text=i18n.t("about.description"))
        self._tech_lbl.configure(
            text=f"{i18n.t('about.tech')}: Python · Tkinter · sv-ttk · PyMuPDF · Pillow · pywin32"
        )


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------
class ModernApp:
    """Prizma Studio – Modern UI shell."""

    _SETTINGS_ID = "__settings__"
    _ABOUT_ID = "__about__"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        i18n.set_language(config.get("language", "ru"))

        root.title(f"{__app_name__} · v{__version__}")
        root.geometry(config.get("window_geometry", "1280x800"))
        root.minsize(1080, 680)

        icon_path = ASSETS_DIR / "icon.ico"
        if icon_path.exists():
            try:
                root.iconbitmap(default=str(icon_path))
            except tk.TclError:
                pass

        apply_modern_theme(root, config.get("theme", "system"))

        # Per-tab state ------------------------------------------------------
        self._panels: dict[str, ttk.Frame] = {}   # tab_id -> frame
        self._paths: dict[str, str] = {}          # tab_id -> filesystem path
        self._counter = 0

        self._build_layout()
        self._refresh_recent()
        self._show_welcome()

        i18n.subscribe(self._retranslate)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Optional drag & drop support if tkinterdnd2 is available.
        self._install_dnd()

    # -- Layout ------------------------------------------------------------
    def _build_layout(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        # Sidebar (spans all rows on the left).
        self.sidebar = ModernSidebar(
            self.root,
            app_name=__app_name__,
            on_open_recent=self._open_path,
            on_clear_recent=self._clear_recent,
        )
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="ns")

        # Top bar.
        self._build_top_bar()

        # Content area (tab bar + active panel).
        self.content = ttk.Frame(self.root, padding=(12, 0, 12, 0))
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(1, weight=1)

        self.tab_bar = BrowserTabBar(
            self.content,
            on_activate=self._activate_tab,
            on_close=self._close_tab,
        )
        self.tab_bar.grid(row=0, column=0, sticky="ew")

        self.panel_host = ttk.Frame(self.content)
        self.panel_host.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self.panel_host.columnconfigure(0, weight=1)
        self.panel_host.rowconfigure(0, weight=1)

        # Log panel.
        self.log_panel = ModernLogPanel(self.root)
        self.log_panel.grid(row=2, column=1, sticky="ew", padx=12, pady=(6, 4))

        # Status bar.
        self._status_var = tk.StringVar(value=i18n.t("status.ready"))
        bar = ttk.Frame(self.root, style="Status.TFrame", padding=(16, 4))
        bar.grid(row=3, column=1, sticky="ew")
        bar.columnconfigure(0, weight=1)
        self._status_lbl = ttk.Label(
            bar, textvariable=self._status_var, style="Status.TLabel",
        )
        self._status_lbl.grid(row=0, column=0, sticky="w")

    def _build_top_bar(self) -> None:
        bar = ttk.Frame(self.root, style="TopBar.TFrame", padding=(16, 12, 16, 8))
        bar.grid(row=0, column=1, sticky="ew")
        bar.columnconfigure(2, weight=1)

        # Left cluster: PDF / PSD open buttons.
        self._pdf_btn = ttk.Button(
            bar, text=f"📄 {i18n.t('topbar.pdf')}",
            style="Accent.TButton", command=self._open_pdf_dialog,
        )
        self._pdf_btn.grid(row=0, column=0, padx=(0, 8))

        self._psd_btn = ttk.Button(
            bar, text=f"🎨 {i18n.t('topbar.psd')}",
            style="Accent.TButton", command=self._open_psd_dialog,
        )
        self._psd_btn.grid(row=0, column=1, padx=(0, 8))

        # Right cluster: Settings, About, Language.
        right = ttk.Frame(bar, style="TopBar.TFrame")
        right.grid(row=0, column=3, sticky="e")

        self._settings_btn = ttk.Button(
            right, text=f"⚙  {i18n.t('topbar.settings')}",
            style="Ghost.TButton", command=self._show_settings,
        )
        self._settings_btn.pack(side="left", padx=(0, 6))

        self._about_btn = ttk.Button(
            right, text=f"ℹ  {i18n.t('topbar.about')}",
            style="Ghost.TButton", command=self._show_about,
        )
        self._about_btn.pack(side="left", padx=(0, 12))

        self._lang_var = tk.StringVar(value=config.get("language", "ru"))
        self._lang_combo = ttk.Combobox(
            right, textvariable=self._lang_var,
            values=["ru", "en"], state="readonly", width=5,
        )
        self._lang_combo.pack(side="left")
        self._lang_combo.bind("<<ComboboxSelected>>", self._on_lang_change)

    # -- Welcome / panel switching ----------------------------------------
    def _clear_panel_host(self) -> None:
        for child in self.panel_host.winfo_children():
            child.grid_forget()

    def _show_welcome(self) -> None:
        self._clear_panel_host()
        if not hasattr(self, "_welcome"):
            self._welcome = WelcomeScreen(
                self.panel_host,
                app_name=__app_name__,
                on_open_pdf=self._open_pdf_dialog,
                on_open_psd=self._open_psd_dialog,
            )
        self._welcome.grid(row=0, column=0, sticky="nsew")

    def _activate_tab(self, tab_id: str) -> None:
        panel = self._panels.get(tab_id)
        if panel is None:
            return
        self._clear_panel_host()
        panel.grid(row=0, column=0, sticky="nsew")
        self.tab_bar.set_active(tab_id)

    def _close_tab(self, tab_id: str) -> None:
        self.tab_bar.remove_tab(tab_id)
        panel = self._panels.pop(tab_id, None)
        self._paths.pop(tab_id, None)
        if panel is not None:
            panel.destroy()
        if not self._panels:
            self._show_welcome()
        else:
            still_active = self.tab_bar.active_id()
            if still_active:
                self._activate_tab(still_active)

    # -- Log helper --------------------------------------------------------
    def _log(self, message: str, level: str = "info") -> None:
        self.log_panel.log(message, level)
        self._status_var.set(message)

    # -- File open flows ---------------------------------------------------
    def _open_pdf_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title=i18n.t("pdf.open"),
            initialdir=config.get("pdf_last_dir") or str(Path.home()),
            filetypes=[("PDF", "*.pdf"), (i18n.t("common.open"), "*.*")],
        )
        if path:
            self._open_path(path)

    def _open_psd_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title=i18n.t("psd.open"),
            initialdir=config.get("psd_in_dir") or str(Path.home()),
            filetypes=[("Photoshop", "*.psd *.psb"),
                       (i18n.t("common.open"), "*.*")],
        )
        if path:
            self._open_path(path)

    def _open_path(self, path: str) -> None:
        """Open ``path`` in a new tab (or focus an existing one)."""
        p = Path(path)
        if not p.exists():
            self._log(f"{i18n.t('error.title')}: {path}", "error")
            return

        # Focus if already open.
        for tid, existing in self._paths.items():
            if existing == str(p):
                self._activate_tab(tid)
                return

        suffix = p.suffix.lower()
        if suffix == ".pdf":
            self._open_pdf_in_tab(str(p))
        elif suffix in (".psd", ".psb"):
            self._open_psd_in_tab(str(p))
        else:
            self._log(f"{i18n.t('error.title')}: {p.suffix}", "error")
            return

        self._push_recent(str(p))

    def _open_pdf_in_tab(self, path: str) -> None:
        self._counter += 1
        tab_id = f"pdf-{self._counter}"
        frame = PdfToolsFrame(self.panel_host, log=self._log)
        self._panels[tab_id] = frame
        self._paths[tab_id] = path
        self.tab_bar.add_tab(tab_id, Path(path).name, kind="pdf")
        # Try to load the file into the freshly created frame.
        self._load_into_frame(frame, path, method="_open_specific")
        config.set("pdf_last_dir", str(Path(path).parent))
        self._activate_tab(tab_id)
        self._log(f"{i18n.t('pdf.opened')} {Path(path).name}", "ok")

    def _open_psd_in_tab(self, path: str) -> None:
        self._counter += 1
        tab_id = f"psd-{self._counter}"
        frame = PsdToolsFrame(self.panel_host, log=self._log)
        self._panels[tab_id] = frame
        self._paths[tab_id] = path
        self.tab_bar.add_tab(tab_id, Path(path).name, kind="psd")
        self._load_into_frame(frame, path, method="_open_specific")
        config.set("psd_in_dir", str(Path(path).parent))
        self._activate_tab(tab_id)
        self._log(f"PSD: {Path(path).name}", "ok")

    def _load_into_frame(self, frame: ttk.Frame, path: str, method: str) -> None:
        """Best-effort: hand the file to the underlying frame.

        The existing PdfToolsFrame / PsdToolsFrame classes were designed
        around their own "Open…" buttons. We try several conventional
        method names; if none is found we simply leave the frame empty and
        the user can press the frame's own Open button.
        """
        candidates = (method, "open_file", "load_file", "load", "_open_path")
        for name in candidates:
            fn = getattr(frame, name, None)
            if callable(fn):
                try:
                    fn(path)
                    return
                except TypeError:
                    try:
                        fn()
                        return
                    except Exception:
                        pass
                except Exception:
                    pass

    # -- Settings / About tabs --------------------------------------------
    def _show_settings(self) -> None:
        if not self.tab_bar.has_tab(self._SETTINGS_ID):
            frame = SettingsFrame(self.panel_host, on_theme_change=self._change_theme)
            self._panels[self._SETTINGS_ID] = frame
            self.tab_bar.add_tab(
                self._SETTINGS_ID, i18n.t("topbar.settings"), kind="settings",
            )
        self._activate_tab(self._SETTINGS_ID)

    def _show_about(self) -> None:
        if not self.tab_bar.has_tab(self._ABOUT_ID):
            frame = AboutFrame(self.panel_host)
            self._panels[self._ABOUT_ID] = frame
            self.tab_bar.add_tab(
                self._ABOUT_ID, i18n.t("topbar.about"), kind="about",
            )
        self._activate_tab(self._ABOUT_ID)

    # -- Recent files ------------------------------------------------------
    def _push_recent(self, path: str) -> None:
        recent = [p for p in config.get("recent_files", []) if p != path]
        recent.insert(0, path)
        recent = recent[:MAX_RECENT]
        config.set("recent_files", recent)
        self._refresh_recent()

    def _clear_recent(self) -> None:
        config.set("recent_files", [])
        self._refresh_recent()
        self._log(i18n.t("sidebar.no_recent"), "info")

    def _refresh_recent(self) -> None:
        self.sidebar.set_recent(list(config.get("recent_files", [])))

    # -- Language / theme changes ----------------------------------------
    def _on_lang_change(self, _event) -> None:
        lang = self._lang_var.get()
        config.set("language", lang)
        i18n.set_language(lang)

    def _change_theme(self, mode: str) -> None:
        apply_modern_theme(self.root, mode)
        self.log_panel.apply_palette()
        self._refresh_recent()  # re-apply hover colours from new palette

    def _retranslate(self) -> None:
        self._status_var.set(i18n.t("status.ready"))
        self._pdf_btn.configure(text=f"📄 {i18n.t('topbar.pdf')}")
        self._psd_btn.configure(text=f"🎨 {i18n.t('topbar.psd')}")
        self._settings_btn.configure(text=f"⚙  {i18n.t('topbar.settings')}")
        self._about_btn.configure(text=f"ℹ  {i18n.t('topbar.about')}")
        # Refresh the labels of built-in tabs (Settings / About) too.
        if self.tab_bar.has_tab(self._SETTINGS_ID):
            self.tab_bar.rename_tab(self._SETTINGS_ID, i18n.t("topbar.settings"))
        if self.tab_bar.has_tab(self._ABOUT_ID):
            self.tab_bar.rename_tab(self._ABOUT_ID, i18n.t("topbar.about"))

    # -- Drag & drop -------------------------------------------------------
    def _install_dnd(self) -> None:
        try:
            from tkinterdnd2 import DND_FILES  # type: ignore
        except Exception:
            return
        try:
            self.root.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
            self.root.dnd_bind("<<Drop>>", self._on_drop)  # type: ignore[attr-defined]
        except Exception:
            # Root wasn't created via TkinterDnD.Tk() – silently skip.
            pass

    def _on_drop(self, event) -> None:
        raw = event.data or ""
        # Windows DnD returns "{c:/a b/one.pdf} {c:/two.pdf}".
        paths: list[str] = []
        current = ""
        in_brace = False
        for ch in raw:
            if ch == "{":
                in_brace = True
                current = ""
            elif ch == "}":
                in_brace = False
                if current:
                    paths.append(current)
                current = ""
            elif ch == " " and not in_brace:
                if current:
                    paths.append(current)
                current = ""
            else:
                current += ch
        if current:
            paths.append(current)
        for p in paths:
            self._open_path(p)

    # -- Shutdown ----------------------------------------------------------
    def _on_close(self) -> None:
        try:
            config.set("window_geometry", self.root.geometry())
        finally:
            self.root.destroy()


def _create_root() -> tk.Tk:
    """Create root – prefer TkinterDnD.Tk() when available for drop support."""
    try:
        from tkinterdnd2 import TkinterDnD  # type: ignore
        return TkinterDnD.Tk()
    except Exception:
        return tk.Tk()


def main() -> None:
    root = _create_root()
    ModernApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
