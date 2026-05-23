#!/usr/bin/env python3
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from yt_dlp import YoutubeDL


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bois Club YouTube Downloader")
        self.geometry("560x310")
        self.minsize(560, 310)

        self.out_dir = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.url_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="audio")
        self.status_var = tk.StringVar(value="Paste a YouTube URL and hit Download.")
        self.progress_var = tk.DoubleVar(value=0.0)
        self._q: queue.Queue = queue.Queue()
        self._busy = False

        self._build_ui()
        self.after(100, self._drain_queue)

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        frm_url = ttk.Frame(self)
        frm_url.pack(fill="x", **pad)
        ttk.Label(frm_url, text="URL:").pack(side="left")
        entry = ttk.Entry(frm_url, textvariable=self.url_var)
        entry.pack(side="left", fill="x", expand=True, padx=(6, 0))
        entry.focus_set()

        frm_dir = ttk.Frame(self)
        frm_dir.pack(fill="x", **pad)
        ttk.Label(frm_dir, text="Save to:").pack(side="left")
        ttk.Entry(frm_dir, textvariable=self.out_dir).pack(
            side="left", fill="x", expand=True, padx=(6, 6)
        )
        ttk.Button(frm_dir, text="Browse…", command=self._choose_dir).pack(side="left")

        frm_mode = ttk.LabelFrame(self, text="Format")
        frm_mode.pack(fill="x", **pad)
        ttk.Radiobutton(
            frm_mode,
            text="Audio (MP3)",
            variable=self.mode_var,
            value="audio",
            command=self._update_button_label,
        ).pack(side="left", padx=(10, 16), pady=4)
        ttk.Radiobutton(
            frm_mode,
            text="Video (highest quality MP4)",
            variable=self.mode_var,
            value="video",
            command=self._update_button_label,
        ).pack(side="left", pady=4)

        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill="x", **pad)
        self.btn = ttk.Button(frm_btn, text="Download MP3", command=self._start)
        self.btn.pack(side="left")
        ttk.Button(frm_btn, text="Open folder", command=self._open_folder).pack(
            side="left", padx=(6, 0)
        )

        ttk.Progressbar(
            self, variable=self.progress_var, maximum=100.0
        ).pack(fill="x", **pad)

        ttk.Label(self, textvariable=self.status_var, wraplength=540, anchor="w").pack(
            fill="x", **pad
        )

        self.bind("<Return>", lambda _e: self._start())

    def _update_button_label(self):
        self.btn.config(
            text="Download MP3" if self.mode_var.get() == "audio" else "Download MP4"
        )

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.out_dir.get() or str(Path.home()))
        if d:
            self.out_dir.set(d)

    def _open_folder(self):
        path = self.out_dir.get()
        if not path or not Path(path).exists():
            return
        if sys.platform == "darwin":
            os.system(f'open "{path}"')
        elif sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            os.system(f'xdg-open "{path}"')

    def _start(self):
        if self._busy:
            return
        url = self.url_var.get().strip()
        if not url:
            messagebox.showinfo("Missing URL", "Paste a YouTube URL first.")
            return
        out = Path(self.out_dir.get()).expanduser()
        out.mkdir(parents=True, exist_ok=True)

        self._busy = True
        self.btn.config(state="disabled")
        self.progress_var.set(0.0)
        self.status_var.set("Starting…")

        mode = self.mode_var.get()
        threading.Thread(
            target=self._download, args=(url, str(out), mode), daemon=True
        ).start()

    def _download(self, url: str, out_dir: str, mode: str):
        if mode == "video":
            opts = {
                "format": "bestvideo*+bestaudio/best",
                "merge_output_format": "mp4",
                "outtmpl": str(Path(out_dir) / "%(title)s.%(ext)s"),
                "noprogress": True,
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [self._hook_video],
            }
        else:
            opts = {
                "format": "bestaudio/best",
                "outtmpl": str(Path(out_dir) / "%(title)s.%(ext)s"),
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "noprogress": True,
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [self._hook_audio],
                "postprocessor_hooks": [self._pp_hook],
            }
        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([url])
            self._q.put(("done", None))
        except Exception as e:
            self._q.put(("error", str(e)))

    def _hook_audio(self, d):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes") or 0
            pct = (done / total * 100) if total else 0
            title = d.get("info_dict", {}).get("title", "")
            self._q.put(("progress", (pct, f"Downloading: {title}")))
        elif status == "finished":
            self._q.put(("progress", (100.0, "Converting to MP3…")))

    def _hook_video(self, d):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes") or 0
            pct = (done / total * 100) if total else 0
            title = d.get("info_dict", {}).get("title", "")
            self._q.put(("progress", (pct, f"Downloading: {title}")))
        elif status == "finished":
            self._q.put(("progress", (100.0, "Merging video + audio…")))

    def _pp_hook(self, d):
        if d.get("status") == "started":
            self._q.put(("progress", (100.0, "Converting to MP3…")))

    def _drain_queue(self):
        try:
            while True:
                kind, payload = self._q.get_nowait()
                if kind == "progress":
                    pct, msg = payload
                    self.progress_var.set(pct)
                    self.status_var.set(msg)
                elif kind == "done":
                    self.progress_var.set(100.0)
                    self.status_var.set(f"Done. Saved to {self.out_dir.get()}")
                    self.btn.config(state="normal")
                    self._busy = False
                elif kind == "error":
                    self.progress_var.set(0.0)
                    self.status_var.set(f"Error: {payload}")
                    self.btn.config(state="normal")
                    self._busy = False
                    messagebox.showerror("Download failed", payload)
        except queue.Empty:
            pass
        self.after(100, self._drain_queue)


if __name__ == "__main__":
    App().mainloop()
