"""Modern theme system for Prizma Studio.

Provides a modern color palette (light/dark) plus custom ttk styles for
sidebar, browser-style tabs, welcome screen and modern log panel.

Colors were chosen to give the classic sv-ttk theme a fresh, slightly
warmer/more contrasty feel. They intentionally avoid the generic
purple/violet gradient look.
"""
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
LIGHT_PALETTE = {
    "bg":            "#F6F7F9",   # window background
    "surface":       "#FFFFFF",   # cards / content area
    "sidebar":       "#EEF0F3",
    "sidebar_hover": "#E1E4EA",
    "border":        "#D8DCE3",
    "text":          "#1B1F27",
    "text_muted":    "#6A7280",
    "accent":        "#2E7DFF",
    "accent_hover":  "#1F63D6",
    "accent_soft":   "#E6EFFF",
    "success":       "#2FA36B",
    "warning":       "#E39B2B",
    "danger":        "#DC4E4E",
    "tab_active":    "#FFFFFF",
    "tab_inactive":  "#E7EAF0",
    "log_bg":        "#FBFBFD",
}

DARK_PALETTE = {
    "bg":            "#171A21",
    "surface":       "#1F232C",
    "sidebar":       "#141720",
    "sidebar_hover": "#242833",
    "border":        "#2C3140",
    "text":          "#E6E8EC",
    "text_muted":    "#8890A0",
    "accent":        "#4C8DFF",
    "accent_hover":  "#6BA0FF",
    "accent_soft":   "#22314D",
    "success":       "#4CC48A",
    "warning":       "#F0B04A",
    "danger":        "#F16B6B",
    "tab_active":    "#1F232C",
    "tab_inactive":  "#161A22",
    "log_bg":        "#141720",
}


# ---------------------------------------------------------------------------
# System theme detection (mirrors core.theme but returned string is normalised)
# ---------------------------------------------------------------------------
def _detect_system_theme() -> str:
    if sys.platform.startswith("win"):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if value == 1 else "dark"
        except OSError:
            pass
    try:
        import darkdetect  # type: ignore
        detected = darkdetect.theme()
        if isinstance(detected, str):
            return detected.lower()
    except Exception:
        pass
    return "light"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
_CURRENT_PALETTE: dict[str, str] = dict(LIGHT_PALETTE)


def get_palette() -> dict[str, str]:
    """Return the palette dict currently in use."""
    return _CURRENT_PALETTE


def apply_modern_theme(root: tk.Misc, mode: str) -> str:
    """Apply sv-ttk theme + modern custom ttk styles.

    Returns the effective mode used ('light' or 'dark').
    """
    global _CURRENT_PALETTE

    import sv_ttk
    effective = _detect_system_theme() if mode == "system" else mode
    if effective not in ("light", "dark"):
        effective = "light"

    sv_ttk.set_theme(effective, root)

    _CURRENT_PALETTE = dict(DARK_PALETTE if effective == "dark" else LIGHT_PALETTE)
    _install_custom_styles(root, _CURRENT_PALETTE)
    return effective


# ---------------------------------------------------------------------------
# Custom ttk styles
# ---------------------------------------------------------------------------
def _install_custom_styles(root: tk.Misc, p: dict[str, str]) -> None:
    style = ttk.Style(root)

    # Root window background (helps eliminate hard color seams).
    try:
        root.configure(background=p["bg"])
    except tk.TclError:
        pass

    # Sidebar --------------------------------------------------------------
    style.configure("Sidebar.TFrame", background=p["sidebar"])
    style.configure("Sidebar.TLabel",
                    background=p["sidebar"],
                    foreground=p["text"])
    style.configure("SidebarMuted.TLabel",
                    background=p["sidebar"],
                    foreground=p["text_muted"])
    style.configure("SidebarBrand.TLabel",
                    background=p["sidebar"],
                    foreground=p["text"],
                    font=("Segoe UI", 14, "bold"))
    style.configure("SidebarHeader.TLabel",
                    background=p["sidebar"],
                    foreground=p["text_muted"],
                    font=("Segoe UI", 9, "bold"))
    style.configure("Sidebar.TButton", padding=(10, 6))

    # Top bar --------------------------------------------------------------
    style.configure("TopBar.TFrame", background=p["bg"])
    style.configure("TopBar.TLabel",
                    background=p["bg"],
                    foreground=p["text_muted"],
                    font=("Segoe UI", 9))

    # Accent button (used on Welcome screen) -------------------------------
    style.configure(
        "Accent.TButton",
        padding=(18, 10),
        font=("Segoe UI", 10, "bold"),
    )

    # Ghost button (subtle, transparent-looking) ---------------------------
    style.configure("Ghost.TButton", padding=(10, 6))

    # Tab bar --------------------------------------------------------------
    style.configure("TabBar.TFrame", background=p["bg"])
    style.configure("Tab.TFrame", background=p["tab_inactive"], relief="flat")
    style.configure("TabActive.TFrame", background=p["tab_active"], relief="flat")
    style.configure("Tab.TLabel",
                    background=p["tab_inactive"],
                    foreground=p["text_muted"])
    style.configure("TabActive.TLabel",
                    background=p["tab_active"],
                    foreground=p["text"],
                    font=("Segoe UI", 10, "bold"))
    style.configure("TabClose.TLabel",
                    background=p["tab_inactive"],
                    foreground=p["text_muted"])
    style.configure("TabCloseActive.TLabel",
                    background=p["tab_active"],
                    foreground=p["text"])

    # Welcome screen -------------------------------------------------------
    style.configure("Welcome.TFrame", background=p["bg"])
    style.configure("WelcomeTitle.TLabel",
                    background=p["bg"],
                    foreground=p["text"],
                    font=("Segoe UI", 26, "bold"))
    style.configure("WelcomeTagline.TLabel",
                    background=p["bg"],
                    foreground=p["text_muted"],
                    font=("Segoe UI", 12))
    style.configure("WelcomeHint.TLabel",
                    background=p["bg"],
                    foreground=p["text_muted"],
                    font=("Segoe UI", 10))

    # Log panel ------------------------------------------------------------
    style.configure("Log.TFrame", background=p["log_bg"])
    style.configure("LogTitle.TLabel",
                    background=p["log_bg"],
                    foreground=p["text"],
                    font=("Segoe UI", 10, "bold"))

    # Status bar -----------------------------------------------------------
    style.configure("Status.TFrame", background=p["bg"])
    style.configure("Status.TLabel",
                    background=p["bg"],
                    foreground=p["text_muted"],
                    font=("Segoe UI", 9))
