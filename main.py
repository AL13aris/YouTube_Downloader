"""YouTube Downloader - Application entry point."""
"""
Copyright (C) 2026 AL13aris

[License]
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

[⚠️ PROJECT STATUS: ARCHIVED / UNMAINTAINED]
- EN: This project is a completed technical study for educational and personal backup purposes only. 
      It is NO LONGER MAINTAINED or updated. Use at your own risk.
- KR: 본 프로젝트는 교육 및 개인 백업 목적의 기술 연구용으로 완결된 프로젝트입니다. 
      현재는 유지보수 및 업데이트가 완전히 중단(Archived)되었으며, 본 코드로 인해 발생하는 모든 책임은 사용자에게 있습니다.
"""
import os
import re
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from downloader import DownloadWorker
from ui_mainwindow import MainWindow
from utils import check_dependencies


def is_youtube_url(url: str) -> bool:
    """Check if a string looks like a valid YouTube URL."""
    pattern = (
        r'^https?://(?:www\.)?'
        r'(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|'
        r'youtu\.be/|'
        r'music\.youtube\.com/)'
    )
    return bool(re.match(pattern, url.strip()))


def wire_worker_signals(worker: DownloadWorker, window: MainWindow) -> None:
    """Connect DownloadWorker signals to MainWindow slots."""
    worker.update_progress.connect(window.update_progress_label)
    worker.progress.connect(window.update_download_progress)
    worker.completed.connect(window.mark_download_completed)
    worker.error.connect(window.mark_download_error)
    worker.error.connect(window.show_error)


def start_download(window: MainWindow) -> None:
    """Validate inputs, create DownloadWorker, wire signals, and start."""
    # Guard against concurrent downloads
    if window._is_downloading:
        QMessageBox.warning(window, "경고",
                            "다운로드가 이미 진행 중입니다.\n현재 다운로드가 완료되면 다시 시도하세요.")
        return

    urls = window.url_textedit.toPlainText().strip()

    if not urls:
        QMessageBox.warning(window, "입력 오류",
                            "최소 하나의 유튜브 URL을 입력하세요.")
        return

    url_list = [u.strip() for u in urls.split('\n') if u.strip()]

    if not url_list:
        QMessageBox.warning(window, "입력 오류",
                            "유효한 유튜브 URL을 입력하세요.")
        return

    # Validate YouTube URLs
    invalid_urls = [u for u in url_list if not is_youtube_url(u)]
    if invalid_urls:
        url_preview = "\n".join(
            u[:60] + "..." if len(u) > 60 else u
            for u in invalid_urls[:5]
        )
        QMessageBox.warning(
            window, "URL 오류",
            f"다음 {len(invalid_urls)}개의 링크가 유효한 유튜브 URL이 아닙니다:\n\n"
            f"{url_preview}\n\n유효한 유튜브 URL만 입력하세요."
        )
        return

    folder_path = window.folder_label.text()
    if folder_path == "폴더가 선택되지 않았습니다":
        QMessageBox.warning(window, "입력 오류",
                            "출력 폴더를 선택하세요.")
        return

    # Validate output directory exists and is writable
    if not os.path.isdir(folder_path):
        QMessageBox.critical(window, "폴더 오류",
                             f"선택한 폴더가 존재하지 않습니다:\n{folder_path}")
        return

    try:
        test_file = os.path.join(folder_path, ".write_test")
        with open(test_file, 'w') as f:
            f.write('')
        os.remove(test_file)
    except PermissionError:
        QMessageBox.critical(window, "폴더 오류",
                             f"폴더에 쓰기 권한이 없습니다:\n{folder_path}")
        return
    except OSError as e:
        QMessageBox.critical(window, "폴더 오류",
                             f"폴더 접근 중 오류가 발생했습니다:\n{e}")
        return

    # Prepare UI for download
    window._is_downloading = True
    window.set_download_ui_enabled(False)
    window.progress_label.setText(f"0/{len(url_list)} 다운로드 중...")
    window.progress_bar.setValue(0)
    window.download_list.clear()
    window.download_items.clear()

    for url in url_list:
        window.download_list.addItem("⏳ 대기 중")

    quality = window.quality_combo.currentText().replace("kbps", "")

    # Extract download type (mp3/mp4)
    download_type_text = window.type_combo.currentText()
    download_type = 'mp3' if 'MP3' in download_type_text else 'mp4'

    # Extract selected resolutions from info table
    resolutions = window.get_selected_resolutions()

    # Extract default video quality for MP4 (e.g., "1080p (FHD)" -> 1080)
    video_quality = 0  # 0 = maximum quality
    if download_type == 'mp4':
        vq_text = window.video_quality_combo.currentText()
        vq_match = re.search(r'(\d+)p', vq_text)
        if vq_match:
            video_quality = int(vq_match.group(1))

    worker = DownloadWorker(url_list, folder_path, quality,
                            download_type=download_type,
                            resolutions=resolutions,
                            video_quality=video_quality)
    window._worker = worker
    wire_worker_signals(worker, window)

    def on_finished(success: int, error: int) -> None:
        window._is_downloading = False
        window.set_download_ui_enabled(True)
        window.progress_bar.setValue(100)

        msg = f"다운로드가 완료되었습니다: {success}개 성공"
        if error:
            msg += f"\n에러: {error}개의 링크를 처리하지 못했습니다"

        QMessageBox.information(window, "다운로드 완료", msg)
        window.update_status("대기 중")

    worker.all_downloads_finished.connect(on_finished)
    worker.start()

    window.update_status("다운로드 중...")


def main() -> int:
    """Initialize and run the application."""
    if not check_dependencies():
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "의존성 검사 실패",
                              "ffmpeg 또는 ffprobe를 찾을 수 없습니다.\n\n"
                              "1. ffmpeg와 ffprobe를 exe와 같은 폴더에 복사하세요\n"
                              "2. 또는 시스템에 ffmpeg를 설치하고 PATH에 추가하세요\n\n"
                              "https://ffmpeg.org/download.html")
        return 1

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("YouTube Downloader")
    app.setApplicationVersion("1.0")

    window = MainWindow()
    window.download_button.clicked.disconnect()
    window.download_button.clicked.connect(lambda: start_download(window))
    window.show()

    return app.exec() or 0


if __name__ == "__main__":
    sys.exit(main())
