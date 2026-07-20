"""PSD Tools tab – Photoshop COM integration (Windows only)."""
from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from core.config import config
from core.i18n import i18n

LogFn = Callable[[str, str], None]


def _is_windows() -> bool:
    return sys.platform.startswith("win")


class PhotoshopBridge:
    """Small wrapper around the Photoshop COM interface."""

    def __init__(self) -> None:
        self.app = None
        self.available = False
        self._init_error: Optional[str] = None
        if not _is_windows():
            self._init_error = "Photoshop COM is Windows-only."
            return
        try:
            # EnsureDispatch generates a cached type library so method
            # lookup (Open, DoJavaScript, ...) works via early binding.
            # Falls back to plain Dispatch if the cache cannot be built.
            try:
                from win32com.client import gencache  # type: ignore
                self.app = gencache.EnsureDispatch("Photoshop.Application")
            except Exception:
                import win32com.client as com  # type: ignore
                self.app = com.Dispatch("Photoshop.Application")
            self.app.Visible = True
            # 3 == psDisplayNoDialogs – prevents "Missing fonts / Color profile"
            # dialogs from blocking Open() and other calls.
            try:
                self.app.DisplayDialogs = 3
            except Exception:
                pass
            self.available = True
        except Exception as exc:
            self._init_error = self._format_exc(exc)

    @staticmethod
    def _format_exc(exc: BaseException) -> str:
        parts = [f"{type(exc).__name__}: {exc}".strip()]
        info = getattr(exc, "excepinfo", None)
        if info and len(info) >= 3 and info[2]:
            parts.append(str(info[2]).strip())
        return " | ".join(p for p in parts if p)

    def error(self) -> str:
        return self._init_error or ""

    def open(self, path: str):
        # Normalise to an absolute Windows path with backslashes.
        try:
            norm = str(Path(path).resolve())
        except Exception:
            norm = path
        try:
            return self.app.Open(norm)
        except Exception as exc:
            raise RuntimeError(self._format_exc(exc)) from exc

    def active_document(self):
        return self.app.ActiveDocument


class PsdToolsFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, log: LogFn) -> None:
        super().__init__(master, padding=(12, 8))
        self._log = log
        self._ps: Optional[PhotoshopBridge] = None
        self._doc = None
        self._psd_path: Optional[Path] = None
        self._layers_index: list[tuple[str, list[int]]] = []

        self._mode_var = tk.StringVar(value="fit")
        self._in_var = tk.StringVar(value=config.get("psd_in_dir"))
        self._out_var = tk.StringVar(value=config.get("psd_out_dir"))

        self._build()
        i18n.subscribe(self._retranslate)

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self._btn_open  = ttk.Button(toolbar, text=i18n.t("psd.open"),    command=self.open_psd)
        self._btn_scan  = ttk.Button(toolbar, text=i18n.t("psd.scan"),    command=self.scan_layers)
        self._btn_unlck = ttk.Button(toolbar, text=i18n.t("psd.unlock"),  command=self.unlock_all)
        self._btn_repl  = ttk.Button(toolbar, text=i18n.t("psd.replace"), command=self.replace_in_selected)
        for i, b in enumerate((self._btn_open, self._btn_scan, self._btn_unlck, self._btn_repl)):
            b.grid(row=0, column=i, padx=(0, 6))

        # Left – layers list
        left = ttk.Frame(self)
        left.grid(row=1, column=0, sticky="ns", padx=(0, 12))

        self._lbl_layers = ttk.Label(left, text=i18n.t("psd.section.layers"),
                                     font=("Segoe UI", 10, "bold"))
        self._lbl_layers.pack(anchor="w", pady=(0, 6))

        self._listbox = tk.Listbox(left, width=42, height=22, activestyle="dotbox")
        self._listbox.pack(fill="y", expand=False)

        sb = ttk.Scrollbar(left, orient="vertical", command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=sb.set)

        # Right – actions + batch
        right = ttk.Frame(self)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(1, weight=1)

        self._lbl_actions = ttk.Label(right, text=i18n.t("psd.section.actions"),
                                      font=("Segoe UI", 10, "bold"))
        self._lbl_actions.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self._lbl_mode = ttk.Label(right, text=i18n.t("psd.mode"))
        self._lbl_mode.grid(row=1, column=0, sticky="w", pady=4)
        self._rb_fit  = ttk.Radiobutton(right, text=i18n.t("psd.mode.fit"),
                                        variable=self._mode_var, value="fit")
        self._rb_fill = ttk.Radiobutton(right, text=i18n.t("psd.mode.fill"),
                                        variable=self._mode_var, value="fill")
        self._rb_fit.grid(row=1, column=1, sticky="w")
        self._rb_fill.grid(row=1, column=2, sticky="w")

        ttk.Separator(right, orient="horizontal").grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=12,
        )

        self._lbl_batch = ttk.Label(right, text=i18n.t("psd.section.batch"),
                                    font=("Segoe UI", 10, "bold"))
        self._lbl_batch.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self._lbl_in = ttk.Label(right, text=i18n.t("psd.in.folder"))
        self._lbl_in.grid(row=4, column=0, sticky="w")
        ttk.Entry(right, textvariable=self._in_var).grid(row=4, column=1, sticky="ew", padx=6)
        self._btn_in = ttk.Button(right, text=i18n.t("common.browse"),
                                  command=lambda: self._pick(self._in_var, "psd_in_dir"))
        self._btn_in.grid(row=4, column=2, sticky="w")

        self._lbl_out = ttk.Label(right, text=i18n.t("psd.out.folder"))
        self._lbl_out.grid(row=5, column=0, sticky="w", pady=4)
        ttk.Entry(right, textvariable=self._out_var).grid(row=5, column=1, sticky="ew", padx=6, pady=4)
        self._btn_out = ttk.Button(right, text=i18n.t("common.browse"),
                                   command=lambda: self._pick(self._out_var, "psd_out_dir"))
        self._btn_out.grid(row=5, column=2, sticky="w", pady=4)

        self._btn_batch = ttk.Button(right, text=i18n.t("psd.batch"),
                                     command=self.batch_replace)
        self._btn_batch.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(12, 0))

        # Warning banner
        self._warn = ttk.Label(self, text="", foreground="#c05555")
        self._warn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def _pick(self, var: tk.StringVar, cfg_key: str) -> None:
        chosen = filedialog.askdirectory(initialdir=var.get() or str(Path.home()))
        if chosen:
            var.set(chosen)
            config.set(cfg_key, chosen)

    # ------------------------------------------------------------------
    # Photoshop init (lazy)
    # ------------------------------------------------------------------
    def _ensure_ps(self) -> bool:
        if self._ps is None:
            self._ps = PhotoshopBridge()
        if not self._ps.available:
            self._warn.configure(
                text=f"{i18n.t('psd.no.photoshop')}  ({self._ps.error()})"
            )
            self._log(i18n.t("psd.no.photoshop"), "error")
            return False
        self._warn.configure(text="")
        return True

    # ------------------------------------------------------------------
    # File
    # ------------------------------------------------------------------
    def open_psd(self) -> None:
        if not self._ensure_ps():
            return
        path = filedialog.askopenfilename(
            title=i18n.t("psd.open"),
            initialdir=config.get("psd_in_dir"),
            filetypes=[("Photoshop", "*.psd *.psb"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self._doc = self._ps.open(path)
            self._psd_path = Path(path)
            config.set("psd_in_dir", str(self._psd_path.parent))
            self._log(f"Opened: {self._psd_path.name}", "ok")
            self.scan_layers()
        except Exception as exc:
            msg = str(exc) or exc.__class__.__name__
            hint = (
                "\n\nВозможные причины:\n"
                "  • В Photoshop открыт модальный диалог — закройте его и повторите\n"
                "  • Файл сейчас открыт/заблокирован (OneDrive/Dropbox sync)\n"
                "  • Путь содержит символы, которых Photoshop не понимает —\n"
                "    попробуйте короткий латинский путь (например C:\\test\\file.psd)\n"
                "  • Photoshop показывает «Missing Fonts / Color Profile» — сначала\n"
                "    откройте файл вручную и ответьте на его вопросы"
            )
            messagebox.showerror(i18n.t("error.title"), f"{msg}{hint}")
            self._log(msg, "error")

    # ------------------------------------------------------------------
    # Scan / unlock
    # ------------------------------------------------------------------
    def scan_layers(self) -> None:
        if not self._ensure_ps() or self._doc is None:
            self._log(i18n.t("psd.no.file"), "warn")
            return
        self._layers_index.clear()
        self._listbox.delete(0, "end")
        max_depth = int(config.get("smart_object_depth", 3))
        self._walk(self._doc, path=[], depth=0, max_depth=max_depth)
        self._log(f"Layers scanned: {len(self._layers_index)}", "info")

    def _walk(self, container, path: list[int], depth: int, max_depth: int) -> None:
        try:
            layer_count = container.Layers.Count
        except Exception:
            return
        for i in range(1, layer_count + 1):
            layer = container.Layers.Item(i)
            name = getattr(layer, "Name", f"Layer {i}")
            indent = "  " * depth
            try:
                kind = getattr(layer, "Kind", None)  # 17 = smart object
            except Exception:
                kind = None
            marker = "  [SO]" if kind == 17 else ""
            self._listbox.insert("end", f"{indent}{name}{marker}")
            self._layers_index.append((name, path + [i]))

            try:
                is_group = layer.Typename == "LayerSet"
            except Exception:
                is_group = False
            if is_group and depth < max_depth:
                self._walk(layer, path + [i], depth + 1, max_depth)

    def unlock_all(self) -> None:
        if not self._ensure_ps() or self._doc is None:
            self._log(i18n.t("psd.no.file"), "warn")
            return
        count = self._unlock_recursive(self._doc, depth=0,
                                       max_depth=int(config.get("smart_object_depth", 3)))
        self._log(f"Unlocked {count} layers", "ok")

    def _unlock_recursive(self, container, depth: int, max_depth: int) -> int:
        unlocked = 0
        try:
            layer_count = container.Layers.Count
        except Exception:
            return 0
        for i in range(1, layer_count + 1):
            layer = container.Layers.Item(i)
            for prop in ("AllLocked", "PixelsLocked", "PositionLocked", "TransparentPixelsLocked"):
                try:
                    setattr(layer, prop, False)
                    unlocked += 1
                except Exception:
                    pass
            try:
                if layer.Typename == "LayerSet" and depth < max_depth:
                    unlocked += self._unlock_recursive(layer, depth + 1, max_depth)
            except Exception:
                pass
        return unlocked

    # ------------------------------------------------------------------
    # Replace photo in Smart Object
    # ------------------------------------------------------------------
    def replace_in_selected(self) -> None:
        if not self._ensure_ps() or self._doc is None:
            self._log(i18n.t("psd.no.file"), "warn")
            return
        sel = self._listbox.curselection()
        if not sel:
            messagebox.showinfo(i18n.t("info.title"), i18n.t("psd.select.layer"))
            return
        name, path = self._layers_index[sel[0]]
        image_path = filedialog.askopenfilename(
            title=i18n.t("psd.replace"),
            filetypes=[("Images", "*.jpg *.jpeg *.png *.tif *.tiff *.bmp"), ("All", "*.*")],
        )
        if not image_path:
            return
        try:
            layer = self._resolve_layer(path)
            self._replace_smart_object(layer, image_path, self._mode_var.get())
            self._log(f"Replaced photo in '{name}'", "ok")
        except Exception as exc:
            messagebox.showerror(i18n.t("error.title"), str(exc))
            self._log(str(exc), "error")

    def _resolve_layer(self, path: list[int]):
        node = self._doc
        for idx in path:
            node = node.Layers.Item(idx)
        return node

    def _replace_smart_object(self, so_layer, image_path: str, mode: str) -> None:
        """Open a Smart Object contents, place a new image, resize (fit/fill), save."""
        self._doc.ActiveLayer = so_layer
        js = 'try{executeAction(stringIDToTypeID("placedLayerEditContents"), undefined, DialogModes.NO);}catch(e){}'
        self._ps.app.DoJavaScript(js)

        so_doc = self._ps.app.ActiveDocument
        try:
            escaped = image_path.replace("\\", "\\\\")
            self._ps.app.DoJavaScript(
                f'var f = new File("{escaped}");'
                f'var d = new ActionDescriptor();'
                f'd.putPath(charIDToTypeID("null"), f);'
                f'd.putEnumerated(charIDToTypeID("FTcs"), charIDToTypeID("QCSt"),'
                f' charIDToTypeID("Qcsa"));'
                f'executeAction(charIDToTypeID("Plc "), d, DialogModes.NO);'
            )
            placed = so_doc.ActiveLayer
            db = so_doc
            target_w = db.Width
            target_h = db.Height
            bounds = placed.Bounds
            src_w = float(bounds[2]) - float(bounds[0])
            src_h = float(bounds[3]) - float(bounds[1])
            if src_w <= 0 or src_h <= 0:
                return
            scale_fit = min(float(target_w) / src_w, float(target_h) / src_h)
            scale_fill = max(float(target_w) / src_w, float(target_h) / src_h)
            scale = scale_fill if mode == "fill" else scale_fit
            pct = scale * 100.0
            placed.Resize(pct, pct, 1)  # 1 = AnchorPosition.MIDDLECENTER

            bounds = placed.Bounds
            cx = (float(bounds[0]) + float(bounds[2])) / 2.0
            cy = (float(bounds[1]) + float(bounds[3])) / 2.0
            placed.Translate(float(target_w) / 2.0 - cx, float(target_h) / 2.0 - cy)

            try:
                placed.Rasterize(0)  # 0 = ENTIRELAYER
            except Exception:
                pass

            so_doc.Save()
        finally:
            so_doc.Close(2)  # 2 = SaveOptions.DONOTSAVECHANGES on temp copy

    # ------------------------------------------------------------------
    # Batch replace
    # ------------------------------------------------------------------
    def batch_replace(self) -> None:
        if not self._ensure_ps():
            return
        in_dir = Path(self._in_var.get() or "")
        out_dir = Path(self._out_var.get() or "")
        if not in_dir.is_dir():
            messagebox.showerror(i18n.t("error.title"), f"Bad in-folder: {in_dir}")
            return
        out_dir.mkdir(parents=True, exist_ok=True)
        images = [p for p in in_dir.iterdir()
                  if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp")]
        if not images:
            messagebox.showinfo(i18n.t("info.title"), "No images found in in-folder")
            return
        sel = self._listbox.curselection()
        if not sel:
            messagebox.showinfo(i18n.t("info.title"), i18n.t("psd.select.layer"))
            return
        name, path = self._layers_index[sel[0]]

        if self._doc is None or self._psd_path is None:
            self._log(i18n.t("psd.no.file"), "warn")
            return

        self._log(f"Batch: {len(images)} image(s) → layer '{name}'", "info")
        for img in images:
            try:
                layer = self._resolve_layer(path)
                self._replace_smart_object(layer, str(img), self._mode_var.get())
                target = out_dir / f"{self._psd_path.stem}__{img.stem}.psd"
                self._doc.SaveAs(str(target))
                self._log(f"Saved: {target.name}", "ok")
            except Exception as exc:
                self._log(f"{img.name}: {exc}", "error")
        self._log(i18n.t("psd.done"), "ok")

    # ------------------------------------------------------------------
    # i18n
    # ------------------------------------------------------------------
    def _retranslate(self) -> None:
        pairs = [
            (self._btn_open,  "psd.open"),
            (self._btn_scan,  "psd.scan"),
            (self._btn_unlck, "psd.unlock"),
            (self._btn_repl,  "psd.replace"),
            (self._btn_batch, "psd.batch"),
            (self._btn_in,    "common.browse"),
            (self._btn_out,   "common.browse"),
            (self._rb_fit,    "psd.mode.fit"),
            (self._rb_fill,   "psd.mode.fill"),
        ]
        for widget, key in pairs:
            widget.configure(text=i18n.t(key))
        self._lbl_layers.configure(text=i18n.t("psd.section.layers"))
        self._lbl_actions.configure(text=i18n.t("psd.section.actions"))
        self._lbl_batch.configure(text=i18n.t("psd.section.batch"))
        self._lbl_mode.configure(text=i18n.t("psd.mode"))
        self._lbl_in.configure(text=i18n.t("psd.in.folder"))
        self._lbl_out.configure(text=i18n.t("psd.out.folder"))
        if self._ps and not self._ps.available:
            self._warn.configure(text=f"{i18n.t('psd.no.photoshop')}  ({self._ps.error()})")
