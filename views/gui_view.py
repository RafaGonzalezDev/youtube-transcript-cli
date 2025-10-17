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
    """
    The main class for the Tkinter-based GUI.

    This class is responsible for building and managing the user interface,
    handling user interactions (e.g., button clicks, text input), and
    coordinating with the TranscriptController to fetch and display
    YouTube video transcripts.
    """
    def __init__(self, root: tk.Tk, controller: Optional[TranscriptController] = None) -> None:
        """
        Initializes the GUI.

        Sets up the main window, state variables, color theme, widget layout,
        and event bindings.

        Args:
            root: The root Tkinter window.
            controller: The controller instance for handling business logic.
        """
        self.root = root
        self.controller = controller or TranscriptController()

        self.root.title("YouTube Transcript Downloader")
        self.root.geometry("960x640")
        self.root.minsize(880, 560)

        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar(value="youtube_transcript")
        self.language_var = tk.StringVar(value=AUTO_LANGUAGE_LABEL)
        self.status_var = tk.StringVar(value="Ready")

        self._colors = {
            "background": "#f8fafc",
            "card": "#ffffff",
            "accent": "#2563eb",
            "accent_hover": "#1d4ed8",
            "muted": "#64748b",
            "border": "#e2e8f0",
            "text": "#0f172a",
        }

        self.current_markdown: Optional[str] = None
        self.current_transcript = None
        self._language_refresh_job: Optional[str] = None
        self._last_language_url: Optional[str] = None

        self._setup_theme()
        self._build_layout()
        self._setup_shortcuts()
        self.url_var.trace_add("write", self._schedule_language_refresh)

    def _setup_theme(self) -> None:
        """Configure a modern-looking ttk theme."""
        self.root.configure(bg=self._colors["background"])

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            # Fall back to the default theme if clam is unavailable.
            pass

        style.configure("TFrame", background=self._colors["background"])
        style.configure("TLabel", background=self._colors["background"], foreground=self._colors["text"])

        style.configure("App.TFrame", background=self._colors["background"])
        style.configure("Card.TFrame", background=self._colors["card"], relief="flat", borderwidth=1)
        style.configure("Preview.TFrame", background=self._colors["background"])

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 18, "bold"),
            foreground=self._colors["text"],
            background=self._colors["background"],
        )
        style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 10),
            foreground=self._colors["muted"],
            background=self._colors["background"],
        )
        style.configure(
            "Section.TLabel",
            font=("Segoe UI", 12, "bold"),
            foreground=self._colors["text"],
            background=self._colors["card"],
        )
        style.configure(
            "FieldLabel.TLabel",
            font=("Segoe UI", 9, "bold"),
            foreground=self._colors["muted"],
            background=self._colors["card"],
        )
        style.configure(
            "Body.TLabel",
            font=("Segoe UI", 9),
            foreground=self._colors["muted"],
            background=self._colors["card"],
        )
        style.configure(
            "Status.TLabel",
            font=("Segoe UI", 9),
            foreground=self._colors["muted"],
            background=self._colors["background"],
        )

        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(14, 10),
            background=self._colors["accent"],
            foreground="#ffffff",
            relief="flat",
        )
        style.map(
            "Accent.TButton",
            background=[
                ("disabled", self._colors["border"]),
                ("pressed", self._colors["accent_hover"]),
                ("active", self._colors["accent_hover"]),
            ],
            foreground=[("disabled", "#ffffff")],
        )

        style.configure(
            "Ghost.TButton",
            font=("Segoe UI", 10),
            padding=(12, 8),
            background=self._colors["card"],
            foreground=self._colors["muted"],
            relief="flat",
        )
        style.map(
            "Ghost.TButton",
            background=[
                ("disabled", self._colors["border"]),
                ("pressed", self._colors["border"]),
                ("active", self._colors["border"]),
            ],
            foreground=[("disabled", "#94a3b8")],
        )

        style.configure(
            "Card.TEntry",
            fieldbackground="#ffffff",
            foreground=self._colors["text"],
            padding=8,
            relief="flat",
        )
        style.map(
            "Card.TEntry",
            foreground=[("disabled", self._colors["muted"])],
            fieldbackground=[("disabled", self._colors["border"])],
        )

        style.configure(
            "Card.TCombobox",
            fieldbackground="#ffffff",
            foreground=self._colors["text"],
            padding=6,
            relief="flat",
        )
        style.map(
            "Card.TCombobox",
            foreground=[("disabled", self._colors["muted"])],
            fieldbackground=[("readonly", "#ffffff")],
        )

        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=self._colors["card"],
            background=self._colors["accent"],
        )

        self.style = style

    def _build_layout(self) -> None:
        """Constructs and arranges all the widgets in the main window."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        container = ttk.Frame(self.root, padding=(28, 24, 28, 20), style="App.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        header = ttk.Frame(container, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="YouTube Transcript Downloader", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Recupera, revisa y guarda transcripciones en cuestión de segundos.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        content = ttk.Frame(container, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew", pady=(24, 0))
        content.columnconfigure(0, weight=4, minsize=420)
        content.columnconfigure(1, weight=6, minsize=460)
        content.rowconfigure(0, weight=1)

        controls_card = ttk.Frame(content, style="Card.TFrame", padding=(24, 24, 24, 24))
        controls_card.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        controls_card.columnconfigure(0, weight=1)
        controls_card.rowconfigure(9, weight=1)

        preview_card = ttk.Frame(content, style="Card.TFrame", padding=(24, 24, 24, 20))
        preview_card.grid(row=0, column=1, sticky="nsew")
        preview_card.columnconfigure(0, weight=1)
        preview_card.rowconfigure(2, weight=1)

        ttk.Label(controls_card, text="Datos del vídeo", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            controls_card,
            text="Pega la URL del vídeo y elige cómo quieres guardar la transcripción.",
            style="Body.TLabel",
            wraplength=320,
        ).grid(row=1, column=0, sticky="w", pady=(4, 18))

        ttk.Label(controls_card, text="Video URL", style="FieldLabel.TLabel").grid(row=2, column=0, sticky="w")
        self.url_entry = ttk.Entry(controls_card, textvariable=self.url_var, style="Card.TEntry")
        self.url_entry.grid(row=3, column=0, sticky="ew", pady=(4, 16))

        ttk.Label(controls_card, text="Filename", style="FieldLabel.TLabel").grid(row=4, column=0, sticky="w")
        self.output_entry = ttk.Entry(controls_card, textvariable=self.output_var, style="Card.TEntry")
        self.output_entry.grid(row=5, column=0, sticky="ew", pady=(4, 16))

        ttk.Label(controls_card, text="Language", style="FieldLabel.TLabel").grid(row=6, column=0, sticky="w")
        language_row = ttk.Frame(controls_card, style="Card.TFrame")
        language_row.grid(row=7, column=0, sticky="ew", pady=(4, 0))
        language_row.columnconfigure(0, weight=1)

        self.language_combo = ttk.Combobox(
            language_row,
            textvariable=self.language_var,
            state="readonly",
            values=[AUTO_LANGUAGE_LABEL],
            style="Card.TCombobox",
        )
        self.language_combo.grid(row=0, column=0, sticky="ew")

        self.refresh_button = ttk.Button(
            language_row,
            text="Actualizar",
            style="Ghost.TButton",
            command=self.refresh_languages,
            takefocus=False,
        )
        self.refresh_button.grid(row=0, column=1, sticky="w", padx=(12, 0))

        ttk.Label(
            controls_card,
            text="Mantén \"Auto\" para detectar el idioma automáticamente.",
            style="Body.TLabel",
            wraplength=280,
        ).grid(row=8, column=0, sticky="w", pady=(8, 0))

        ttk.Frame(controls_card, style="Card.TFrame").grid(row=9, column=0, sticky="nsew")

        button_row = ttk.Frame(controls_card, style="Card.TFrame")
        button_row.grid(row=10, column=0, sticky="ew", pady=(24, 0))
        button_row.columnconfigure(0, weight=2, uniform="buttons")
        button_row.columnconfigure(1, weight=2, uniform="buttons")
        button_row.columnconfigure(2, weight=1, uniform="buttons")

        self.fetch_button = ttk.Button(
            button_row,
            text="Fetch Transcript",
            style="Accent.TButton",
            command=self.fetch_transcript,
            takefocus=False,
        )
        self.fetch_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.download_button = ttk.Button(
            button_row,
            text="Save",
            style="Accent.TButton",
            command=self.download_transcript,
            state="disabled",
            takefocus=False,
        )
        self.download_button.grid(row=0, column=1, sticky="ew", padx=4)

        clear_button = ttk.Button(
            button_row,
            text="Clear",
            style="Ghost.TButton",
            command=self.clear_fields,
            takefocus=False,
        )
        clear_button.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        self.progress = ttk.Progressbar(controls_card, mode="indeterminate", style="Accent.Horizontal.TProgressbar")
        self.progress.grid(row=11, column=0, sticky="ew", pady=(18, 0))
        self.progress.grid_remove()

        preview_header = ttk.Frame(preview_card, style="Card.TFrame")
        preview_header.grid(row=0, column=0, sticky="ew")
        preview_header.columnconfigure(0, weight=1)

        ttk.Label(preview_header, text="Transcript Preview", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self.preview_info = ttk.Label(preview_header, text="", style="Body.TLabel")
        self.preview_info.grid(row=0, column=1, sticky="e")

        ttk.Label(
            preview_card,
            text="Consulta el borrador en Markdown y haz ajustes antes de exportarlo.",
            style="Body.TLabel",
            wraplength=340,
        ).grid(row=1, column=0, sticky="w", pady=(12, 14))

        # Use a subtle border to separate the preview area from the background.
        preview_container = tk.Frame(
            preview_card,
            bg=self._colors["background"],
            highlightbackground=self._colors["border"],
            highlightcolor=self._colors["border"],
            highlightthickness=1,
            bd=0,
        )
        preview_container.grid(row=2, column=0, sticky="nsew")
        preview_container.columnconfigure(0, weight=1)
        preview_container.rowconfigure(0, weight=1)

        self.preview_text = scrolledtext.ScrolledText(
            preview_container,
            wrap=tk.WORD,
            undo=False,
            font=("JetBrains Mono", 10),
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            background=self._colors["background"],
            foreground=self._colors["text"],
            insertbackground=self._colors["accent"],
            padx=16,
            pady=16,
        )
        self.preview_text.grid(row=0, column=0, sticky="nsew")

        status_frame = ttk.Frame(container, style="App.TFrame", padding=(0, 24, 0, 0))
        status_frame.grid(row=2, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        ttk.Separator(status_frame, orient="horizontal").grid(row=0, column=0, sticky="ew")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.grid(row=1, column=0, sticky="w", pady=(8, 0))

    def fetch_transcript(self) -> None:
        """Starts the process of fetching a transcript for the given URL."""
        if not self._validate_url():
            return

        requested_language = self.language_var.get().strip()
        language = None if requested_language == AUTO_LANGUAGE_LABEL else requested_language

        url = self.url_var.get().strip()
        self._set_loading(True, "Fetching transcript...")

        thread = threading.Thread(target=self._fetch_worker, args=(url, language), daemon=True)
        thread.start()

    def download_transcript(self) -> None:
        """Opens a save dialog to download the fetched transcript as a Markdown file."""
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
        """Forces a refresh of the available transcript languages for the current URL."""
        self._auto_refresh_languages(force=True)

    def clear_fields(self) -> None:
        """Resets all input fields and the preview area to their default states."""
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
        """
        Schedules a delayed refresh of the language list.

        This is triggered when the user types in the URL entry field, and it
        avoids making excessive requests while the user is still typing.
        """
        if self._language_refresh_job:
            try:
                self.root.after_cancel(self._language_refresh_job)
            except Exception:
                pass
        self._language_refresh_job = self.root.after(600, self._auto_refresh_languages)

    def _auto_refresh_languages(self, force: bool = False) -> None:
        """
        Automatically refreshes the language list if the URL has changed.

        Args:
            force: If True, forces a refresh even if the URL hasn't changed.
        """
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
        """
        Initiates the background thread to fetch available languages.

        Args:
            url: The YouTube video URL.
            notify: Whether to show a status update to the user.
            use_loading: Whether to show the main loading indicator.
        """
        if use_loading:
            self._set_loading(True, "Checking languages...")
        elif notify:
            self.status_var.set("Checking languages...")
        thread = threading.Thread(
            target=self._languages_worker, args=(url, notify, use_loading), daemon=True
        )
        thread.start()

    def _set_language_options(self, languages: list[str]) -> None:
        """
        Updates the language dropdown with a new list of languages.

        Args:
            languages: A list of language codes.
        """
        unique_values = [AUTO_LANGUAGE_LABEL] + sorted(set(languages))
        current = self.language_var.get()
        self.language_combo["values"] = unique_values
        if current not in unique_values:
            self.language_var.set(AUTO_LANGUAGE_LABEL)

    def _languages_worker(self, url: str, notify: bool, use_loading: bool) -> None:
        """
        The background worker that calls the controller to list languages.

        This runs in a separate thread to avoid blocking the GUI.

        Args:
            url: The YouTube video URL.
            notify: Whether to show a status update to the user.
            use_loading: Whether to show the main loading indicator.
        """
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
        """
        Handles the successful retrieval of the language list.

        This is called on the main GUI thread via `root.after()`.

        Args:
            url: The URL for which languages were fetched.
            manual: A list of manually created language codes.
            generated: A list of auto-generated language codes.
            notify: Whether to show a status update to the user.
            use_loading: Whether the main loading indicator was active.
        """
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
        """
        Handles errors that occur while retrieving the language list.

        This is called on the main GUI thread via `root.after()`.

        Args:
            url: The URL for which the language fetch failed.
            message: The error message.
            notify: Whether to show a status update to the user.
            use_loading: Whether the main loading indicator was active.
        """
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
        """
        The background worker that calls the controller to fetch the transcript.

        This runs in a separate thread to avoid blocking the GUI.

        Args:
            url: The YouTube video URL.
            language: The selected language code, or None for automatic.
        """
        try:
            transcript, markdown = self.controller.fetch_transcript(url, language)
            self.root.after(0, self._fetch_success, transcript, markdown)
        except ValueError as exc:
            self.root.after(0, self._operation_error, str(exc))
        except Exception as exc:
            logger.exception("Unexpected error while fetching transcript")
            self.root.after(0, self._operation_error, f"An unexpected error occurred: {exc}")

    def _fetch_success(self, transcript, markdown: str) -> None:
        """
        Handles the successful retrieval of the transcript.

        This is called on the main GUI thread via `root.after()`.

        Args:
            transcript: The fetched transcript object.
            markdown: The formatted Markdown string.
        """
        self._set_loading(False)
        self.download_button.config(state="normal")
        self.status_var.set(f"Transcript fetched in {transcript.language}")
        self.current_markdown = markdown
        self.current_transcript = transcript
        self._set_language_options(transcript.available_languages)
        self._last_language_url = transcript.url

        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, markdown)
        word_count = len(markdown.split())
        self.preview_info.config(text=f"{word_count} words")

    def _operation_error(self, message: str) -> None:
        """
        Displays an error message to the user and resets the loading state.

        Args:
            message: The error message to display.
        """
        self._set_loading(False)
        self.status_var.set("Error")
        messagebox.showerror("Error", message)

    def _set_loading(self, is_loading: bool, status: Optional[str] = None) -> None:
        """
        Enables or disables the loading state of the UI.

        When loading, it disables input widgets and shows a progress bar.

        Args:
            is_loading: True to enable the loading state, False to disable it.
            status: An optional status message to display.
        """
        if status:
            self.status_var.set(status)
        widgets = [
            self.fetch_button,
            self.download_button,
            self.refresh_button,
            self.url_entry,
            self.output_entry,
            self.language_combo,
        ]
        state = "disabled" if is_loading else "normal"
        for widget in widgets:
            try:
                widget.config(state=state)
            except Exception:
                pass
        if is_loading:
            try:
                self.progress.start(10)
            except Exception:
                logger.debug("Failed to start progress bar animation", exc_info=True)
        else:
            try:
                self.progress.stop()
            except Exception:
                logger.debug("Failed to stop progress bar animation", exc_info=True)

    def _validate_url(self) -> bool:
        """Validates that the entered URL is a valid YouTube URL."""
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
        """Validates that a filename has been entered."""
        output_file = self.output_var.get().strip()
        if not output_file:
            messagebox.showerror("Error", "Please specify a filename")
            return False
        return True

    def _setup_shortcuts(self) -> None:
        """Binds keyboard shortcuts to common actions."""
        self.root.bind("<Return>", lambda _event: self.fetch_transcript())
        self.root.bind("<Control-s>", lambda _event: self.download_transcript())


def run_gui() -> None:
    """
    Initializes and runs the YouTube Transcript Downloader GUI.

    This function sets up the main Tkinter window, loads private fonts,
    creates the controller and GUI instances, and starts the main event loop.
    """
    fonts_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
    load_private_fonts(os.path.abspath(fonts_dir))

    root = tk.Tk()
    controller = TranscriptController()
    YouTubeTranscriptGUI(root, controller)
    root.mainloop()
