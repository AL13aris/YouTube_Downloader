"""Utility functions for the YouTube Downloader application."""

import json
import os
import re
import subprocess
import sys


# Settings file path - saved next to the executable (PyInstaller onedir mode)
def _get_app_dir() -> str:
    """Return the directory containing the executable or script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


_SETTINGS_FILE = os.path.join(_get_app_dir(), "settings.json")


def _load_settings() -> dict:
    """Load settings from JSON file. Returns empty dict if not found."""
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_settings(settings: dict) -> None:
    """Save settings to JSON file."""
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get_saved_folder() -> str | None:
    """Get the last saved output folder path, or None if not saved/invalid."""
    settings = _load_settings()
    folder = settings.get("output_folder")
    if folder and os.path.isdir(folder):
        return folder
    return None


def save_folder(folder: str) -> None:
    """Save the output folder path to settings."""
    settings = _load_settings()
    settings["output_folder"] = folder
    _save_settings(settings)


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """Sanitize a string to be used as a valid filename.

    Removes or replaces characters that are invalid on Windows/macOS/Linux.
    Truncates to 200 characters to avoid filesystem limits.

    Args:
        name: Raw filename string.
        replacement: Character to replace invalid chars with.

    Returns:
        Sanitized filename string.
    """
    # Remove control characters
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)

    # Remove or replace invalid filename characters
    # Windows: < > : " / \ | ? *
    # macOS: :
    # Linux: /
    name = re.sub(r'[<>:"/\\|?*]', replacement, name)

    # Remove leading/trailing spaces and dots (Windows issue)
    name = name.strip().strip('.')

    # Limit length
    if len(name) > 200:
        name = name[:200]

    return name if name else "untitled"


def _locate_bundled_ffmpeg() -> str | None:
    """Search for bundled ffmpeg.exe in priority order.

    Returns the directory path if found, None otherwise.
    Priority: exe directory → _internal → _MEIPASS → project directory.
    """
    candidates: list[str] = []

    if getattr(sys, 'frozen', False):
        # PyInstaller onedir: exe and bundled files are in the same folder
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates.append(exe_dir)
        candidates.append(os.path.join(exe_dir, '_internal'))
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            candidates.append(meipass)
    else:
        candidates.append(os.path.dirname(os.path.abspath(__file__)))

    for candidate in candidates:
        if (os.path.exists(os.path.join(candidate, 'ffmpeg.exe'))
                and os.path.exists(os.path.join(candidate, 'ffprobe.exe'))):
            return candidate
    return None


def check_dependencies() -> bool:
    """Check if required dependencies are available.

    Verifies that ffmpeg and ffprobe are installed and accessible.
    When running as a frozen (PyInstaller) app,优先 checks the executable's
    directory for bundled ffmpeg/ffprobe, then falls back to system PATH.
    """
    bundled_dir = _locate_bundled_ffmpeg()
    if bundled_dir and bundled_dir not in os.environ.get('PATH', ''):
        os.environ['PATH'] = bundled_dir + os.pathsep + os.environ['PATH']

    missing = []

    for tool in ['ffmpeg', 'ffprobe']:
        try:
            result = subprocess.run(
                [tool, '-version'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                missing.append(tool)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            missing.append(tool)
        except Exception:
            missing.append(tool)

    if missing:
        return False

    return True
