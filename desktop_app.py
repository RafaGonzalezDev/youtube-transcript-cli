import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse
import re
import requests
from bs4 import BeautifulSoup

# Import functions from the original app
from app import extract_video_id, get_transcript, format_transcript_to_markdown

class YouTubeTranscriptGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Transcript Downloader")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        # Variables
        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar(value="youtube_transcript")
        self.status_var = tk.StringVar(value="Ready")
        self.current_transcript = None
        self.current_url = None

        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="YouTube Transcript Downloader", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URL input
        ttk.Label(main_frame, text="YouTube URL:").grid(row=1, column=0, sticky=tk.W, pady=10)
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=10, padx=(10, 0))

        
        # Output filename
        ttk.Label(main_frame, text="Filename:").grid(row=2, column=0, sticky=tk.W, pady=10)
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=50)
        output_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=10, padx=(10, 0))
        
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=25)
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.columnconfigure(2, weight=1)
        
        self.fetch_button = ttk.Button(buttons_frame, text="Fetch Transcript", 
                                      command=self.fetch_transcript, takefocus=False, padding=(8, 4))
        self.fetch_button.grid(row=0, column=0, padx=5, sticky=(tk.W, tk.E))
        
        self.download_button = ttk.Button(buttons_frame, text="Download Transcript", 
                                         command=self.download_transcript, state='disabled', takefocus=False, padding=(8, 4))
        self.download_button.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        clear_button = ttk.Button(buttons_frame, text="Clear", command=self.clear_fields, takefocus=False, padding=(8, 4))
        clear_button.grid(row=0, column=2, padx=5, sticky=(tk.W, tk.E))
        
        # Preview area
        preview_label = ttk.Label(main_frame, text="Preview:")
        preview_label.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))

        preview_frame = ttk.Frame(main_frame)
        preview_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=15, width=70, wrap=tk.WORD, padx=10, pady=10)
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Status bar
        status_frame = ttk.Frame(self.root, padding=(10, 5))
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
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
        self.fetch_button.config(state='disabled')
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
        self.fetch_button.config(state='normal')
        self.download_button.config(state='normal')  # Enable download button
        self.status_var.set("Transcript fetched successfully")
        
        # Store transcript and URL for later download
        self.current_transcript = content
        self.current_url = url
        
        # Show preview
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, content)
    
    def _fetch_error(self, error_message):
        self.fetch_button.config(state='normal')
        self.status_var.set("Error fetching transcript")
        messagebox.showerror("Error", error_message)

def main():
    root = tk.Tk()
    app = YouTubeTranscriptGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()