# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 my3w-98
#
# This file is part of HEIC Convert.
# https://github.com/my3w-98/heic-convert
"""HEIC Convert — bulk HEIC/HEIF image converter GUI."""

from __future__ import annotations

import argparse
import ctypes
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from converter import OUTPUT_FORMATS, collect_heic_files, convert_batch

APP_TITLE = "HEIC Convert"
APP_ID = "Tools.HEICConvert"
ACCENT = "#C45C26"
BG = "#1A1B1E"
PANEL = "#24262B"
TEXT = "#E8E6E3"
MUTED = "#9A9690"
BORDER = "#3A3D45"


def set_windows_app_identity() -> None:
    """Make the taskbar / Alt-Tab entry show as HEIC Convert instead of python."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:  # noqa: BLE001 — best-effort on older Windows
        pass
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(APP_TITLE)
    except Exception:  # noqa: BLE001
        pass


class HeicConvertApp(tk.Tk):
    def __init__(self, initial_paths: list[Path] | None = None) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("780x620")
        self.minsize(680, 520)
        self.configure(bg=BG)

        self.files: list[Path] = []
        self.output_dir = tk.StringVar(value="")
        self.format_name = tk.StringVar(value="JPEG")
        self.quality = tk.IntVar(value=90)
        self.overwrite = tk.BooleanVar(value=False)
        self.recursive = tk.BooleanVar(value=True)
        self.open_when_done = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Add HEIC/HEIF files or a folder to begin.")
        self._busy = False

        self._style()
        self._build()
        if initial_paths:
            self.add_paths(initial_paths)

    def _style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", background=BG, foreground=TEXT, fieldbackground=PANEL)
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 18))
        style.configure("TCheckbutton", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure(
            "TButton",
            background=PANEL,
            foreground=TEXT,
            borderwidth=0,
            focuscolor=PANEL,
            font=("Segoe UI", 10),
            padding=(14, 8),
        )
        style.map("TButton", background=[("active", BORDER)])
        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="#FFFFFF",
            font=("Segoe UI Semibold", 10),
            padding=(18, 10),
        )
        style.map("Accent.TButton", background=[("active", "#A84B1F"), ("disabled", "#5C4033")])
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor=PANEL,
            background=ACCENT,
            bordercolor=PANEL,
            lightcolor=ACCENT,
            darkcolor=ACCENT,
        )
        style.configure(
            "TCombobox",
            fieldbackground=PANEL,
            background=PANEL,
            foreground=TEXT,
            arrowcolor=TEXT,
            padding=6,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", PANEL)],
            selectbackground=[("readonly", BORDER)],
            selectforeground=[("readonly", TEXT)],
        )
        style.configure(
            "Treeview",
            background=PANEL,
            foreground=TEXT,
            fieldbackground=PANEL,
            borderwidth=0,
            rowheight=26,
            font=("Segoe UI", 9),
        )
        style.configure("Treeview.Heading", background=BORDER, foreground=TEXT, font=("Segoe UI Semibold", 9))
        style.map("Treeview", background=[("selected", BORDER)], foreground=[("selected", TEXT)])

    def _build(self) -> None:
        root = ttk.Frame(self, padding=20)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text=APP_TITLE, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            root,
            text="Bulk-convert Apple HEIC/HEIF photos to JPEG, PNG, WebP, and more.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 16))

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Add files…", command=self.pick_files).pack(side="left")
        ttk.Button(actions, text="Add folder…", command=self.pick_folder).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Clear list", command=self.clear_files).pack(side="left", padx=(8, 0))

        list_frame = ttk.Frame(root, style="Card.TFrame", padding=8)
        list_frame.pack(fill="both", expand=True)

        cols = ("name", "folder")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="extended")
        self.tree.heading("name", text="File")
        self.tree.heading("folder", text="Location")
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("folder", width=420, anchor="w")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        opts = ttk.Frame(root)
        opts.pack(fill="x", pady=(14, 0))

        ttk.Label(opts, text="Output format").grid(row=0, column=0, sticky="w")
        fmt = ttk.Combobox(
            opts,
            textvariable=self.format_name,
            values=list(OUTPUT_FORMATS.keys()),
            state="readonly",
            width=12,
        )
        fmt.grid(row=1, column=0, sticky="w", pady=(4, 0))
        fmt.bind("<<ComboboxSelected>>", lambda _e: self._sync_quality_state())

        ttk.Label(opts, text="Quality").grid(row=0, column=1, sticky="w", padx=(24, 0))
        quality_row = ttk.Frame(opts)
        quality_row.grid(row=1, column=1, sticky="w", padx=(24, 0), pady=(4, 0))
        self.quality_scale = ttk.Scale(
            quality_row,
            from_=1,
            to=100,
            orient="horizontal",
            variable=self.quality,
            length=140,
            command=lambda _v: self.quality_label.configure(text=str(self.quality.get())),
        )
        self.quality_scale.pack(side="left")
        self.quality_label = ttk.Label(quality_row, text="90", width=4)
        self.quality_label.pack(side="left", padx=(8, 0))

        ttk.Label(opts, text="Output folder").grid(row=0, column=2, sticky="w", padx=(24, 0))
        out_row = ttk.Frame(opts)
        out_row.grid(row=1, column=2, sticky="ew", padx=(24, 0), pady=(4, 0))
        opts.columnconfigure(2, weight=1)
        ttk.Entry(out_row, textvariable=self.output_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(out_row, text="Browse…", command=self.pick_output).pack(side="left", padx=(8, 0))

        checks = ttk.Frame(root)
        checks.pack(fill="x", pady=(12, 0))
        ttk.Checkbutton(checks, text="Scan folders recursively", variable=self.recursive).pack(side="left")
        ttk.Checkbutton(checks, text="Overwrite existing files", variable=self.overwrite).pack(
            side="left", padx=(16, 0)
        )
        ttk.Checkbutton(
            checks,
            text="Open output in Microsoft Photos when done",
            variable=self.open_when_done,
        ).pack(side="left", padx=(16, 0))

        bottom = ttk.Frame(root)
        bottom.pack(fill="x", pady=(16, 0))
        self.progress = ttk.Progressbar(bottom, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 10))
        ttk.Label(bottom, textvariable=self.status, style="Muted.TLabel").pack(anchor="w")
        ttk.Button(bottom, text="Convert", style="Accent.TButton", command=self.start_convert).pack(
            anchor="e", pady=(12, 0)
        )

        self._sync_quality_state()

    def _sync_quality_state(self) -> None:
        lossy = OUTPUT_FORMATS[self.format_name.get()]["lossy"]
        state = "normal" if lossy else "disabled"
        self.quality_scale.configure(state=state)

    def pick_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select HEIC/HEIF images",
            filetypes=[
                ("HEIC / HEIF", "*.heic *.heif *.HEIC *.HEIF"),
                ("All files", "*.*"),
            ],
        )
        if paths:
            self.add_paths([Path(p) for p in paths])

    def pick_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select folder containing HEIC/HEIF images")
        if folder:
            self.add_paths([Path(folder)])

    def pick_output(self) -> None:
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_dir.set(folder)

    def clear_files(self) -> None:
        self.files.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.status.set("List cleared. Add HEIC/HEIF files or a folder to begin.")

    def add_paths(self, paths: list[Path]) -> None:
        collected = collect_heic_files(paths, recursive=self.recursive.get())
        existing = {p.resolve() for p in self.files}
        added = 0
        for path in collected:
            if path in existing:
                continue
            self.files.append(path)
            self.tree.insert("", "end", values=(path.name, str(path.parent)))
            added += 1

        if not self.output_dir.get() and self.files:
            self.output_dir.set(str(self.files[0].parent / "converted"))

        skipped = len(collected) - added
        msg = f"{len(self.files)} image(s) ready"
        if added:
            msg += f" · {added} added"
        if skipped:
            msg += f" · {skipped} already listed"
        if not collected:
            msg = "No HEIC/HEIF files found in the selection."
        self.status.set(msg)

    def start_convert(self) -> None:
        if self._busy:
            return
        if not self.files:
            messagebox.showinfo(APP_TITLE, "Add at least one HEIC/HEIF file first.")
            return

        out = self.output_dir.get().strip()
        if not out:
            messagebox.showinfo(APP_TITLE, "Choose an output folder.")
            return

        output_dir = Path(out)
        self._busy = True
        self.progress.configure(value=0, maximum=len(self.files))
        self.status.set(f"Converting 0 / {len(self.files)}…")

        def worker() -> None:
            def on_progress(done: int, total: int, result) -> None:
                self.after(0, lambda: self._on_progress(done, total, result))

            results = convert_batch(
                sources=list(self.files),
                output_dir=output_dir,
                format_name=self.format_name.get(),
                quality=self.quality.get(),
                overwrite=self.overwrite.get(),
                on_progress=on_progress,
            )
            self.after(0, lambda: self._on_done(results, output_dir))

        threading.Thread(target=worker, daemon=True).start()

    def _on_progress(self, done: int, total: int, result) -> None:
        self.progress.configure(value=done)
        label = "ok" if result.ok else "failed"
        self.status.set(f"Converting {done} / {total}… last: {result.source.name} ({label})")

    def _on_done(self, results, output_dir: Path) -> None:
        self._busy = False
        ok = sum(1 for r in results if r.ok)
        fail = len(results) - ok
        self.status.set(f"Done — {ok} converted, {fail} failed → {output_dir}")
        if fail:
            errors = "\n".join(f"{r.source.name}: {r.error}" for r in results if not r.ok)[:1200]
            messagebox.showwarning(APP_TITLE, f"Finished with {fail} error(s):\n\n{errors}")
        else:
            messagebox.showinfo(APP_TITLE, f"Converted {ok} image(s) to:\n{output_dir}")

        if self.open_when_done.get() and ok:
            first = next((r.destination for r in results if r.ok and r.destination), None)
            self._open_in_photos(first or output_dir)

    def _open_in_photos(self, target: Path) -> None:
        """Open a converted image (or folder) with Microsoft Photos / default viewer."""
        if not target.exists():
            return
        try:
            if target.is_file():
                subprocess.Popen(
                    ["cmd", "/c", "start", "", f"ms-photos:viewer?fileName={target}"],
                    shell=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                return
            os.startfile(target)  # noqa: S606
        except OSError:
            try:
                os.startfile(target)  # noqa: S606
            except OSError:
                pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional HEIC/HEIF files or folders to preload",
    )
    return parser.parse_args(argv)


def main() -> None:
    set_windows_app_identity()
    args = parse_args()
    initial = [Path(p) for p in args.paths if p]
    app = HeicConvertApp(initial_paths=initial or None)
    app.mainloop()


if __name__ == "__main__":
    main()
