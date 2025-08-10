import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter import font as tkfont
import threading
import os
import glob
import platform
import ctypes
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse
import re
import requests
from bs4 import BeautifulSoup

# Import functions from the original app
from app import extract_video_id, get_transcript, format_transcript_to_markdown


def load_private_fonts(font_dir: str) -> None:
    """Load TTF/OTF fonts privately for this process on Windows.

    Fonts added with FR_PRIVATE are visible only to the current process,
    which is ideal for bundling fonts with the app without installing system-wide.
    """
    try:
        if platform.system() != 'Windows':
            return
        if not font_dir or not os.path.isdir(font_dir):
            return
        font_paths = []
        font_paths.extend(glob.glob(os.path.join(font_dir, "*.ttf")))
        font_paths.extend(glob.glob(os.path.join(font_dir, "*.otf")))
        if not font_paths:
            return
        FR_PRIVATE = 0x10
        added_any = False
        for font_path in font_paths:
            try:
                res = ctypes.windll.gdi32.AddFontResourceExW(str(font_path), FR_PRIVATE, 0)
                if res > 0:
                    added_any = True
            except Exception:
                # Ignore failures for individual files
                pass
        if added_any:
            try:
                HWND_BROADCAST = 0xFFFF
                WM_FONTCHANGE = 0x001D
                ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0, 0, 1000, None)
            except Exception:
                pass
    except Exception:
        # Silently ignore font loading issues; app will fall back to system fonts
        pass

class YouTubeTranscriptGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Transcript Downloader")
        self.root.geometry("900x640")
        self.root.minsize(700, 480)

        # Variables
        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar(value="youtube_transcript")
        self.status_var = tk.StringVar(value="Ready")
        self.current_transcript = None
        self.current_url = None

        self._setup_style()
        self.setup_ui()
        self._setup_shortcuts()
        
    def setup_ui(self):
        # Root grid config
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # Header
        header = ttk.Frame(self.root, style='Header.TFrame')
        header.grid(row=0, column=0, sticky=(tk.W, tk.E))
        header.columnconfigure(0, weight=1)
        title = ttk.Label(header, text="YouTube Transcript Downloader", style='Header.TLabel')
        subtitle = ttk.Label(header, text="Minimal, clean and fast", style='HeaderSub.TLabel')
        title.grid(row=0, column=0, sticky=tk.W, padx=24, pady=(18, 2))
        subtitle.grid(row=1, column=0, sticky=tk.W, padx=24, pady=(0, 16))

        # Content area (card)
        container = ttk.Frame(self.root, style='App.TFrame', padding=16)
        container.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        container.columnconfigure(0, weight=1)

        card = ttk.Frame(container, style='Card.TFrame', padding=20)
        card.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        card.columnconfigure(1, weight=1)
        card.rowconfigure(6, weight=1)

        # URL input
        ttk.Label(card, text="YouTube URL", style='Label.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        self.url_entry = ttk.Entry(card, textvariable=self.url_var, width=50, style='Input.TEntry')
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(12, 0))

        # Output filename
        ttk.Label(card, text="Filename", style='Label.TLabel').grid(row=1, column=0, sticky=tk.W, pady=(0, 8))
        self.output_entry = ttk.Entry(card, textvariable=self.output_var, width=50, style='Input.TEntry')
        self.output_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(12, 0))

        # Buttons
        buttons_frame = ttk.Frame(card, style='Card.TFrame')
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=18, sticky=(tk.W, tk.E))
        for c in range(3):
            buttons_frame.columnconfigure(c, weight=1)

        self.fetch_button = ttk.Button(
            buttons_frame,
            text="Fetch Transcript",
            command=self.fetch_transcript,
            takefocus=False,
            style='Accent.TButton',
            padding=(12, 8),
        )
        self.fetch_button.grid(row=0, column=0, padx=6, sticky=(tk.W, tk.E))

        self.download_button = ttk.Button(
            buttons_frame,
            text="Download Transcript",
            command=self.download_transcript,
            state='disabled',
            takefocus=False,
            style='Primary.TButton',
            padding=(12, 8),
        )
        self.download_button.grid(row=0, column=1, padx=6, sticky=(tk.W, tk.E))

        clear_button = ttk.Button(
            buttons_frame,
            text="Clear",
            command=self.clear_fields,
            takefocus=False,
            style='Secondary.TButton',
            padding=(12, 8),
        )
        clear_button.grid(row=0, column=2, padx=6, sticky=(tk.W, tk.E))

        # Progress bar
        self.progress = ttk.Progressbar(card, mode='indeterminate', style='Thin.Horizontal.TProgressbar')
        self.progress.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 6))
        self.progress.grid_remove()

        # Preview label
        preview_label = ttk.Label(card, text="Preview", style='Section.TLabel')
        preview_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(8, 6))

        # Preview area
        preview_frame = ttk.Frame(card, style='CardInner.TFrame')
        preview_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            height=16,
            width=70,
            wrap=tk.WORD,
            padx=12,
            pady=12,
            undo=False,
        )
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.preview_text.configure(font=self.font_mono, background=self.colors['editor_bg'], foreground=self.colors['text'])

        # Status bar
        status_frame = ttk.Frame(self.root, padding=(16, 8), style='Status.TFrame')
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W, style='Status.TLabel')
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        


    def get_video_title(self, url):
        """Extract video title from YouTube URL."""
        try:
            video_id = extract_video_id(url)
            if not video_id:
                return None
            
            # Use YouTube's oEmbed API to get video title
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = requests.get(oembed_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('title', '')
            
        except Exception:
            # Fallback: try to scrape title from page
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    title_tag = soup.find('title')
                    if title_tag:
                        title = title_tag.text.strip()
                        # Remove " - YouTube" suffix if present
                        if title.endswith(' - YouTube'):
                            title = title[:-10]
                        return title
            except Exception:
                pass
        
        return None
    

    

    
    def clear_fields(self):
        self.url_var.set("")
        self.output_var.set("youtube_transcript")
        self.preview_text.delete(1.0, tk.END)
        self.status_var.set("Ready")
        self.current_transcript = None
        self.current_url = None
        self.download_button.config(state='disabled')
    
    def validate_url(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return False
        
        if not urlparse(url).scheme:
            messagebox.showerror("Error", "Invalid URL format")
            return False
        
        video_id = extract_video_id(url)
        if not video_id:
            messagebox.showerror("Error", "Could not extract video ID from the provided URL")
            return False
        
        return True
    
    def validate_filename(self):
        output_file = self.output_var.get().strip()
        if not output_file:
            messagebox.showerror("Error", "Please specify a filename")
            return False
        return True
    
    def fetch_transcript(self):
        if not self.validate_url():
            return
        
        # Disable button and update status
        self._set_loading(True)
        self.status_var.set("Fetching transcript...")
        
        # Run fetch in separate thread
        thread = threading.Thread(target=self._fetch_worker)
        thread.daemon = True
        thread.start()
    
    def download_transcript(self):
        if not self.validate_filename():
            return
        
        if not self.current_transcript:
            messagebox.showerror("Error", "No transcript available. Please fetch transcript first.")
            return
        
        # Open file dialog to choose save location
        filename = self.output_var.get().strip()
        if not filename.endswith('.md'):
            filename += '.md'
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
            initialfile=filename
        )
        
        if save_path:
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(self.current_transcript)
                
                self.status_var.set(f"Transcript saved to {save_path}")
                messagebox.showinfo("Success", f"Transcript successfully saved to {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def _fetch_worker(self):
        try:
            url = self.url_var.get().strip()
            
            video_id = extract_video_id(url)
            transcript = get_transcript(video_id, None)  # No language specified
            markdown_content = format_transcript_to_markdown(transcript, url)
            
            # Update UI in main thread
            self.root.after(0, self._fetch_success, markdown_content, url)
            
        except (ValueError, TranscriptsDisabled, NoTranscriptFound) as e:
            self.root.after(0, self._fetch_error, str(e))
        except Exception as e:
            self.root.after(0, self._fetch_error, f"An unexpected error occurred: {e}")
    
    def _fetch_success(self, content, url):
        self._set_loading(False)
        self.download_button.config(state='normal')
        self.status_var.set("Transcript fetched successfully")
        
        # Store transcript and URL for later download
        self.current_transcript = content
        self.current_url = url
        
        # Show preview
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, content)
    
    def _fetch_error(self, error_message):
        self._set_loading(False)
        self.status_var.set("Error fetching transcript")
        messagebox.showerror("Error", error_message)

    def _set_loading(self, is_loading: bool):
        if is_loading:
            self.fetch_button.config(state='disabled')
            self.url_entry.config(state='disabled')
            self.output_entry.config(state='disabled')
            self.progress.grid()
            try:
                self.progress.start(10)
            except Exception:
                pass
        else:
            self.fetch_button.config(state='normal')
            self.url_entry.config(state='normal')
            self.output_entry.config(state='normal')
            try:
                self.progress.stop()
            except Exception:
                pass
            self.progress.grid_remove()

    def _setup_shortcuts(self):
        # Enter to fetch when focus in entries
        self.root.bind('<Return>', lambda e: self.fetch_transcript())
        # Ctrl+S to download
        self.root.bind('<Control-s>', lambda e: self.download_transcript())

    def _setup_style(self):
        # Color palette and fonts
        self.colors = {
            'bg': '#F5F6F8',
            'card': '#FFFFFF',
            'header_bg': '#111827',
            'header_text': '#FFFFFF',
            'text': '#111827',
            'muted': '#6B7280',
            'border': '#E5E7EB',
            'primary': '#2563EB',
            'primary_hover': '#1D4ED8',
            'editor_bg': '#FAFAFA',
        }

        self.root.configure(bg=self.colors['bg'])

        # Resolve available font families (prefer private ones if loaded)
        families = set(tkfont.families(self.root))

        def pick_font(preferred_list, default_name):
            for name in preferred_list:
                if name in families:
                    return name
            return default_name

        base_family = pick_font([
            'JetBrains Mono', 'JetBrainsMono', 'Consolas', 'Cascadia Mono', 'Cascadia Code'
        ], 'Consolas')
        # Use the same monospaced family for the whole app
        mono_family = base_family

        self.font_base = (base_family, 10)
        self.font_title = (base_family, 18, 'bold')
        self.font_subtitle = (base_family, 11)
        self.font_status = (base_family, 9)
        self.font_mono = (base_family, 10)

        style = ttk.Style()
        # Prefer a modern theme if available
        preferred_theme = 'clam'
        try:
            style.theme_use(preferred_theme)
        except Exception:
            pass

        # Update Tk named default fonts for wider consistency
        try:
            tkfont.nametofont('TkDefaultFont').configure(family=self.font_base[0], size=self.font_base[1])
            tkfont.nametofont('TkTextFont').configure(family=self.font_base[0], size=self.font_base[1])
            tkfont.nametofont('TkHeadingFont').configure(family=self.font_base[0], size=self.font_base[1] + 2)
            tkfont.nametofont('TkFixedFont').configure(family=self.font_mono[0], size=self.font_mono[1])
        except Exception:
            pass

        # General styles
        style.configure('App.TFrame', background=self.colors['bg'])
        style.configure('Card.TFrame', background=self.colors['card'])
        style.configure('CardInner.TFrame', background=self.colors['card'])

        style.configure('TLabel', background=self.colors['card'], foreground=self.colors['text'], font=self.font_base)
        style.configure('Label.TLabel', background=self.colors['card'], foreground=self.colors['muted'], font=self.font_base)
        style.configure('Section.TLabel', background=self.colors['card'], foreground=self.colors['text'], font=('Segoe UI', 11, 'bold'))

        style.configure('Input.TEntry', padding=8)

        # Header styles
        style.configure('Header.TFrame', background=self.colors['header_bg'])
        style.configure('Header.TLabel', background=self.colors['header_bg'], foreground=self.colors['header_text'], font=self.font_title)
        style.configure('HeaderSub.TLabel', background=self.colors['header_bg'], foreground='#D1D5DB', font=self.font_subtitle)

        # Buttons
        style.configure('Primary.TButton', font=self.font_base, padding=8)
        style.configure('Secondary.TButton', font=self.font_base, padding=8)
        style.configure('Accent.TButton', font=self.font_base, padding=8, foreground='white', background=self.colors['primary'])
        style.map('Accent.TButton',
                  background=[('active', self.colors['primary_hover']), ('!disabled', self.colors['primary'])],
                  foreground=[('!disabled', 'white')])

        # Status bar
        style.configure('Status.TFrame', background=self.colors['bg'])
        style.configure('Status.TLabel', background=self.colors['bg'], foreground=self.colors['muted'], font=self.font_status)

        # Progressbar
        style.configure(
            'Thin.Horizontal.TProgressbar',
            thickness=6,
            background=self.colors['primary'],
            troughcolor=self.colors['border'],
            bordercolor=self.colors['border']
        )

def main():
    # Load bundled fonts privately (Windows only)
    fonts_dir = os.path.join(os.path.dirname(__file__), 'assets', 'fonts')
    load_private_fonts(fonts_dir)

    root = tk.Tk()
    app = YouTubeTranscriptGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()