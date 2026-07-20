"""Sanity check for Prizma Studio Modern UI.

Run this script BEFORE launching ``main_modern.py`` for the first time
to verify that every required Python dependency and internal module
imports cleanly. It prints a colour-free, symbol-based report so the
output looks fine in every terminal.

Usage
-----
    python test_modern_ui.py
"""
from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path

REQUIRED = [
    # (import name, PyPI package, is required?)
    ("tkinter",     "tkinter (stdlib)", True),
    ("sv_ttk",      "sv-ttk",           True),
    ("fitz",        "PyMuPDF",          True),
    ("PIL",         "Pillow",           True),
    ("darkdetect",  "darkdetect",       True),
    ("tkinterdnd2", "tkinterdnd2",      False),   # optional: drag & drop
    ("win32com",    "pywin32",          False),   # optional: Windows/PSD only
]

INTERNAL = [
    "core",
    "core.config",
    "core.i18n",
    "core.theme_modern",
    "core.modern_widgets",
    "modules.pdf_tools_tab",
    "modules.psd_tools_tab",
]


def _print_row(icon: str, label: str, detail: str = "") -> None:
    print(f"  {icon}  {label:<28} {detail}")


def check_python() -> bool:
    ok = sys.version_info >= (3, 9)
    _print_row("✓" if ok else "✕",
               f"Python {platform.python_version()}",
               "(need >= 3.9)")
    return ok


def check_external() -> tuple[int, int]:
    print("\nExternal packages:")
    missing_required = 0
    total = 0
    for mod, pkg, required in REQUIRED:
        total += 1
        try:
            importlib.import_module(mod)
            _print_row("✓", pkg, "installed")
        except Exception as exc:
            icon = "✕" if required else "○"
            _print_row(icon, pkg, f"missing ({exc})")
            if required:
                missing_required += 1
    return missing_required, total


def check_internal() -> int:
    print("\nInternal modules:")
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    missing = 0
    for mod in INTERNAL:
        try:
            importlib.import_module(mod)
            _print_row("✓", mod, "ok")
        except Exception as exc:
            missing += 1
            _print_row("✕", mod, f"failed – {exc}")
    return missing


def main() -> int:
    print("=" * 60)
    print("  Prizma Studio – Modern UI dependency check")
    print("=" * 60)
    py_ok = check_python()
    ext_missing, _ = check_external()
    int_missing = check_internal()

    print("\n" + "-" * 60)
    if py_ok and ext_missing == 0 and int_missing == 0:
        print("  All good ✓   You can now run:  python main_modern.py")
        return 0

    print("  Issues found:")
    if not py_ok:
        print("    • Upgrade Python to 3.9 or newer.")
    if ext_missing:
        print(f"    • {ext_missing} required package(s) missing – run:")
        print("        pip install -r requirements.txt")
    if int_missing:
        print(f"    • {int_missing} internal module(s) failed to import.")
        print("      Make sure you are inside the ‘prizma’ folder.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
