"""Download manager for YouTube Downloader."""

import os
import re
import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal
from utils import sanitize_filename, _locate_bundled_ffmpeg


class DownloadWorker(QThread):
    """Background worker that downloads videos from YouTube."""

    # Signals for UI updates
    progress = pyqtSignal(str, float)       # title, percentage
    completed = pyqtSignal(str)             # filename
    error = pyqtSignal(str, str)            # url, error_message
    status = pyqtSignal(str)                # status message
    update_progress = pyqtSignal(int, int, str)  # current, total, title
    all_downloads_finished = pyqtSignal(int, int)  # success, error

    def __init__(self, urls, folder_path, quality, download_type='mp3',
                  resolutions=None, video_quality=0):
        super().__init__()
        self.urls = urls
        self.folder_path = folder_path
        self.quality = quality
        self.download_type = download_type  # 'mp3' or 'mp4'
        self.resolutions = resolutions or []  # Per-video resolution selections
        self.video_quality = video_quality  # Default resolution for MP4 (0 = max)
        self._is_running = True

    def stop(self):
        """Signal the worker to stop."""
        self._is_running = False

    def run(self):
        """Download all URLs sequentially."""
        app_dir = _locate_bundled_ffmpeg() or '.'
        success_count = 0
        error_count = 0

        for index, url in enumerate(self.urls, 1):
            if not self._is_running:
                break

            self.update_progress.emit(index, len(self.urls), "")

            try:
                # Determine resolution for this video
                selected_resolution = 0
                if self.resolutions and (index - 1) < len(self.resolutions):
                    selected_resolution = self.resolutions[index - 1]

                # Build yt-dlp options based on download type
                if self.download_type == 'mp3':
                    quality_map = {
                        "128kbps": "128",
                        "192kbps": "192",
                        "320kbps": "320",
                    }
                    audio_quality = quality_map.get(self.quality, "192")

                    ydl_opts = {
                        'outtmpl': os.path.join(self.folder_path, '%(title)s.%(ext)s'),
                        'format': 'bestaudio/best',
                        'quiet': True,
                        'no_warnings': True,
                        'bin_dir': app_dir,
                        'ffmpeg_location': app_dir,
                        'postprocessors': [
                            {
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': audio_quality,
                            }
                        ],
                        'progress_hooks': [
                            lambda d, u=index: self._progress_hook(d, u)
                        ],
                    }
                else:  # mp4
                    ydl_opts = {
                        'outtmpl': os.path.join(self.folder_path, '%(title)s.mp4'),
                        'quiet': True,
                        'no_warnings': True,
                        'bin_dir': app_dir,
                        'ffmpeg_location': app_dir,
                        'merge_output_format': 'mp4',
                        'format_sort': ['res', 'vcodec:avc1', 'acodec'],
                        'progress_hooks': [
                            lambda d, u=index: self._progress_hook(d, u)
                        ],
                    }

                    # Apply resolution filter: per-video selection first, then default
                    effective_resolution = selected_resolution if selected_resolution > 0 else self.video_quality
                    if effective_resolution > 0:
                        ydl_opts['format'] = f'bestvideo[height<={effective_resolution}]+bestaudio[lang^=ko]/bestvideo[height<={effective_resolution}]+bestaudio/best[height<={effective_resolution}]'
                    else:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'Unknown')
                    self.update_progress.emit(index, len(self.urls), title)

                    # Determine output filename
                    if self.download_type == 'mp3':
                        # Find the MP3 file
                        for f in os.listdir(self.folder_path):
                            if f.startswith(title) and f.endswith('.mp3'):
                                filename = f
                                break
                        else:
                            filename = f"{title}.mp3"
                    else:
                        # Find the MP4 file
                        for f in os.listdir(self.folder_path):
                            if f.startswith(title) and f.endswith('.mp4'):
                                filename = f
                                break
                        else:
                            filename = f"{title}.mp4"

                    self.completed.emit(filename)
                    success_count += 1

            except Exception as e:
                self.error.emit(url, str(e))
                error_count += 1

        if self._is_running:
            self.status.emit("모든 다운로드가 완료되었습니다")
        self.all_downloads_finished.emit(success_count, error_count)

    def _progress_hook(self, d, index):
        """Handle download progress updates."""
        if d['status'] == 'downloading':
            percentage = d.get('_percent_str', '0%')
            try:
                pct = float(percentage.replace('%', ''))
            except ValueError:
                pct = 0
            self.progress.emit(d.get('filename', ''), pct)
