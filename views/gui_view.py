from __future__ import annotations

import logging
import os
import threading
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

import ctypes
import glob
import platform

from core import TranscriptController

logger = logging.getLogger(__name__)

# GUI text constants
AUTO_LANGUAGE_LABEL = "Auto"


def load_private_fonts(font_dir: str) -> None:
    """Load bundled fonts privately on Windows without installing them system-wide."""
    try:
        if platform.system() != "Windows":
            return
        if not font_dir or not os.path.isdir(font_dir):
            return
        font_paths = glob.glob(os.path.join(font_dir, "*.ttf")) + glob.glob(os.path.join(font_dir, "*.otf"))
        if not font_paths:
            return
        added_any = False
        FR_PRIVATE = 0x10
        for font_path in font_paths:
            try:
                result = ctypes.windll.gdi32.AddFontResourceExW(str(font_path), FR_PRIVATE, 0)
                if result > 0:
                    added_any = True
            except Exception:
                logger.debug("Failed to register font %s", font_path, exc_info=True)
        if added_any:
            HWND_BROADCAST = 0xFFFF
            WM_FONTCHANGE = 0x001D
            try:
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST, WM_FONTCHANGE, 0, 0, 0, 1000, None
                )
            except Exception:
                logger.debug("Failed to broadcast font change", exc_info=True)
    except Exception:
        logger.debug("Unexpected error while loading private fonts", exc_info=True)


class YouTubeTranscriptGUI:
    def __init__(self, root: tk.Tk, controller: Optional[TranscriptController] = None) -> None:
        self.root = root
        self.controller = controller or TranscriptController()

        self.root.title("YouTube Transcript Downloader")
        self.root.geometry("720x520")
        self.root.minsize(600, 420)

        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar(value="youtube_transcript")
        self.language_var = tk.StringVar(value=AUTO_LANGUAGE_LABEL)
        self.status_var = tk.StringVar(value="Ready")

        self.current_markdown: Optional[str] = None
        self.current_transcript = None
        self._language_refresh_job: Optional[str] = None
        self._last_language_url: Optional[str] = None

        self._build_layout()
        self._setup_shortcuts()
        self.url_var.trace_add("write", self._schedule_language_refresh)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        container = ttk.Frame(self.root, padding=20)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(6, weight=1)

        header = ttk.Label(container, text="YouTube Transcript Downloader", font=("", 14, "bold"))
        header.grid(row=0, column=0, sticky="w")

        description = ttk.Label(container, text="Paste a YouTube link, fetch the transcript, then save it as Markdown.")
        description.grid(row=1, column=0, sticky="w", pady=(2, 16))

        form = ttk.Frame(container)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Video URL").grid(row=0, column=0, sticky="w", pady=4)
        self.url_entry = ttk.Entry(form, textvariable=self.url_var)
        self.url_entry.grid(row=0, column=1, sticky="ew", pady=4, padx=(12, 0))

        ttk.Label(form, text="Filename").grid(row=1, column=0, sticky="w", pady=4)
        self.output_entry = ttk.Entry(form, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=1, sticky="ew", pady=4, padx=(12, 0))

        ttk.Label(form, text="Language").grid(row=2, column=0, sticky="w", pady=4)
        language_row = ttk.Frame(form)
        language_row.grid(row=2, column=1, sticky="ew", pady=4, padx=(12, 0))
        language_row.columnconfigure(0, weight=1)

        self.language_combo = ttk.Combobox(
            language_row,
            textvariable=self.language_var,
            state="readonly",
            values=[AUTO_LANGUAGE_LABEL],
        )
        self.language_combo.grid(row=0, column=0, sticky="ew")

        button_row = ttk.Frame(container)
        button_row.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        for col in range(3):
            button_row.columnconfigure(col, weight=1)

        self.fetch_button = ttk.Button(button_row, text="Fetch", command=self.fetch_transcript, takefocus=False)
        self.fetch_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.download_button = ttk.Button(
            button_row,
            text="Save",
            command=self.download_transcript,
            state="disabled",
            takefocus=False,
        )
        self.download_button.grid(row=0, column=1, sticky="ew", padx=6)

        clear_button = ttk.Button(button_row, text="Clear", command=self.clear_fields, takefocus=False)
        clear_button.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        self.progress = ttk.Progressbar(container, mode="indeterminate")
        self.progress.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        self.progress.grid_remove()

        preview_header = ttk.Frame(container)
        preview_header.grid(row=5, column=0, sticky="ew", pady=(20, 6))
        preview_header.columnconfigure(0, weight=1)

        ttk.Label(preview_header, text="Transcript Preview").grid(row=0, column=0, sticky="w")
        self.preview_info = ttk.Label(preview_header, text="", foreground="grey")
        self.preview_info.grid(row=0, column=1, sticky="e")

        preview_frame = ttk.Frame(container, relief="groove", borderwidth=1)
        preview_frame.grid(row=6, column=0, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            height=14,
            wrap=tk.WORD,
            undo=False,
            font=("", 10),
        )
        self.preview_text.grid(row=0, column=0, sticky="nsew")

        status_frame = ttk.Frame(container)
        status_frame.grid(row=7, column=0, sticky="ew", pady=(12, 0))
        status_frame.columnconfigure(0, weight=1)

        ttk.Separator(status_frame, orient="horizontal").grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor="w")
        self.status_label.grid(row=1, column=0, sticky="ew")

    def fetch_transcript(self) -> None:
        if not self._validate_url():
            return

        requested_language = self.language_var.get().strip()
        language = None if requested_language == AUTO_LANGUAGE_LABEL else requested_language

        url = self.url_var.get().strip()
        self._set_loading(True, "Fetching transcript...")

        thread = threading.Thread(target=self._fetch_worker, args=(url, language), daemon=True)
        thread.start()

    def download_transcript(self) -> None:
        if not self._validate_filename():
            return
        if not self.current_markdown:
            messagebox.showerror("Error", "No transcript available. Please fetch transcript first.")
            return

        filename = self.output_var.get().strip()
        if not filename.endswith(".md"):
            filename += ".md"

        save_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
            initialfile=filename,
        )

        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as handle:
                    handle.write(self.current_markdown)
                self.status_var.set(f"Transcript saved to {save_path}")
                messagebox.showinfo("Success", f"Transcript successfully saved to {save_path}")
            except Exception as exc:
                logger.exception("Failed to save transcript to disk")
                messagebox.showerror("Error", f"Failed to save file: {exc}")

    def refresh_languages(self) -> None:
        self._auto_refresh_languages(force=True)

    def clear_fields(self) -> None:
        if self._language_refresh_job:
            self.root.after_cancel(self._language_refresh_job)
            self._language_refresh_job = None
        self._last_language_url = None
        self.url_var.set("")
        self.output_var.set("youtube_transcript")
        self.language_var.set(AUTO_LANGUAGE_LABEL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_info.config(text="")
        self.status_var.set("Ready")
        self.current_markdown = None
        self.current_transcript = None
        self.download_button.config(state="disabled")
        self.language_combo["values"] = [AUTO_LANGUAGE_LABEL]

    def _schedule_language_refresh(self, *_args) -> None:
        if self._language_refresh_job:
            try:
                self.root.after_cancel(self._language_refresh_job)
            except Exception:
                pass
        self._language_refresh_job = self.root.after(600, self._auto_refresh_languages)

    def _auto_refresh_languages(self, force: bool = False) -> None:
        self._language_refresh_job = None
        url = self.url_var.get().strip()
        if not url:
            self._set_language_options([])
            self._last_language_url = None
            if force:
                self.status_var.set("Ready")
            return
        try:
            self.controller.validate_and_extract_video_id(url)
        except ValueError:
            self._set_language_options([])
            self._last_language_url = None
            if force:
                self.status_var.set("Please provide a valid YouTube URL")
            return
        if not force and self._last_language_url == url:
            return
        self._load_languages(url, notify=force, use_loading=force)

    def _load_languages(self, url: str, notify: bool, use_loading: bool) -> None:
        if use_loading:
            self._set_loading(True, "Checking languages...")
        elif notify:
            self.status_var.set("Checking languages...")
        thread = threading.Thread(
            target=self._languages_worker, args=(url, notify, use_loading), daemon=True
        )
        thread.start()

    def _set_language_options(self, languages: list[str]) -> None:
        unique_values = [AUTO_LANGUAGE_LABEL] + sorted(set(languages))
        current = self.language_var.get()
        self.language_combo["values"] = unique_values
        if current not in unique_values:
            self.language_var.set(AUTO_LANGUAGE_LABEL)

    def _languages_worker(self, url: str, notify: bool, use_loading: bool) -> None:
        try:
            manual, generated = self.controller.list_languages(url)
            self.root.after(0, self._languages_success, url, manual, generated, notify, use_loading)
        except ValueError as exc:
            self.root.after(0, self._languages_error, url, str(exc), notify, use_loading)
        except Exception as exc:
            logger.exception("Unexpected error while listing languages")
            self.root.after(
                0,
                self._languages_error,
                url,
                f"An unexpected error occurred: {exc}",
                notify,
                use_loading,
            )

    def _languages_success(
        self, url: str, manual: list[str], generated: list[str], notify: bool, use_loading: bool
    ) -> None:
        if use_loading:
            self._set_loading(False)
        unique = sorted(set(manual) | set(generated))
        self._set_language_options(unique)
        if self.url_var.get().strip() == url:
            self._last_language_url = url
        if notify:
            manual_count = len(set(manual))
            generated_count = len(set(generated))
            summary = []
            if manual_count:
                summary.append(f"{manual_count} manual")
            if generated_count:
                summary.append(f"{generated_count} generated")
            if not summary:
                summary.append("no transcripts")
            self.status_var.set(f"Languages refreshed: {', '.join(summary)}")
        else:
            current_status = self.status_var.get().lower()
            if "fetching transcript" in current_status:
                return
            if unique:
                self.status_var.set(f"Detected {len(unique)} transcript languages")
            else:
                self.status_var.set("No transcripts available for this video")

    def _languages_error(self, url: str, message: str, notify: bool, use_loading: bool) -> None:
        if use_loading:
            self._set_loading(False)
        if notify:
            self._operation_error(message)
        else:
            logger.debug("Automatic language lookup failed for %s: %s", url, message)
            if self.status_var.get().lower().startswith("fetching"):
                return
            self.status_var.set("Could not load transcript languages automatically")

    def _fetch_worker(self, url: str, language: Optional[str]) -> None:
        try:
            transcript, markdown = self.controller.fetch_transcript(url, language)
            self.root.after(0, self._fetch_success, transcript, markdown)
        except ValueError as exc:
            self.root.after(0, self._operation_error, str(exc))
        except Exception as exc:
            logger.exception("Unexpected error while fetching transcript")
            self.root.after(0, self._operation_error, f"An unexpected error occurred: {exc}")

    def _fetch_success(self, transcript, markdown: str) -> None:
        self._set_loading(False)
        self.download_button.config(state="normal")
        self.status_var.set(f"Transcript fetched in {transcript.language}")
        self.current_markdown = markdown
        self.current_transcript = transcript
        self._set_language_options(transcript.available_languages)
        if transcript.language in transcript.available_languages:
            self.language_var.set(transcript.language)
        self._last_language_url = transcript.url

        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, markdown)
        word_count = len(markdown.split())
        self.preview_info.config(text=f"{word_count} words")

    def _operation_error(self, message: str) -> None:
        self._set_loading(False)
        self.status_var.set("Error")
        messagebox.showerror("Error", message)

    def _set_loading(self, is_loading: bool, status: Optional[str] = None) -> None:
        if status:
            self.status_var.set(status)
        widgets = [self.fetch_button, self.url_entry, self.output_entry, self.language_combo]
        state = "disabled" if is_loading else "normal"
        for widget in widgets:
            try:
                widget.config(state=state)
            except Exception:
                pass
        if is_loading:
            self.progress.grid()
            try:
                self.progress.start(10)
            except Exception:
                logger.debug("Failed to start progress bar animation", exc_info=True)
        else:
            try:
                self.progress.stop()
            except Exception:
                logger.debug("Failed to stop progress bar animation", exc_info=True)
            self.progress.grid_remove()

    def _validate_url(self) -> bool:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return False
        try:
            self.controller.validate_and_extract_video_id(url)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return False
        return True

    def _validate_filename(self) -> bool:
        output_file = self.output_var.get().strip()
        if not output_file:
            messagebox.showerror("Error", "Please specify a filename")
            return False
        return True

    def _setup_shortcuts(self) -> None:
        self.root.bind("<Return>", lambda _event: self.fetch_transcript())
        self.root.bind("<Control-s>", lambda _event: self.download_transcript())


def run_gui() -> None:
    fonts_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
    load_private_fonts(os.path.abspath(fonts_dir))

    root = tk.Tk()
    controller = TranscriptController()
    YouTubeTranscriptGUI(root, controller)
    root.mainloop()
