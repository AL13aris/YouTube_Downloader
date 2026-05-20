"""Main window UI for YouTube Downloader."""
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
import sys
from PyQt6.QtWidgets import (QMainWindow, QTextEdit, QComboBox, QPushButton,
                             QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
                             QMessageBox, QLabel, QListWidget, QProgressBar,
                             QStatusBar, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from utils import get_saved_folder, save_folder


class ResolutionCheckWorker(QThread):
    """Background worker to fetch resolution info for each URL."""
    finished = pyqtSignal(list)  # List of dicts: {url, title, resolutions}
    error = pyqtSignal(str, str)  # url, error_message

    def __init__(self, urls):
        super().__init__()
        self.urls = urls

    def run(self):
        import yt_dlp
        from utils import _locate_bundled_ffmpeg
        results = []
        for url in self.urls:
            try:
                app_dir = _locate_bundled_ffmpeg() or '.'
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'bin_dir': app_dir,
                    'ffmpeg_location': app_dir,
                    'format_sort': ['res', 'vcodec:avc1', 'acodec'],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', '제목 없음')
                    # Collect unique resolutions from available formats
                    resolutions = set()
                    for f in info.get('formats', []):
                        if f.get('height') and f.get('vcodec') != 'none':
                            resolutions.add(f['height'])
                    resolutions = sorted(resolutions, reverse=True)
                    results.append({
                        'url': url,
                        'title': title,
                        'resolutions': resolutions,
                    })
            except Exception as e:
                self.error.emit(url, str(e))
                results.append({
                    'url': url,
                    'title': '정보 조회 실패',
                    'resolutions': [],
                })
        self.finished.emit(results)


class MainWindow(QMainWindow):
    """Main application window with URL input, quality selector,
    progress display, and download management."""

    def __init__(self):
        super().__init__()

        # Set window title and size
        self.setWindowTitle("YouTube Downloader")
        self.resize(650, 650)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("대기 중")

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # URL input area
        url_label = QLabel("유튜브 URL 입력 (한 줄에 하나씩):")
        self.url_textedit = QTextEdit()
        self.url_textedit.setPlaceholderText(
            "여기에 유튜브 URL을 붙여넣으세요 (한 줄에 하나씩)"
        )

        main_layout.addWidget(url_label)
        main_layout.addWidget(self.url_textedit)

        # Resolution check button
        self.check_button = QPushButton("화질 확인")
        self.check_button.clicked.connect(self.check_resolutions)
        main_layout.addWidget(self.check_button)

        # Video info table
        self.info_table = QTableWidget()
        self.info_table.setColumnCount(4)
        self.info_table.setHorizontalHeaderLabels(["#", "제목", "지원 화질", "선택 화질"])
        header = self.info_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.info_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.info_table.setVisible(False)
        main_layout.addWidget(self.info_table)

        # Progress display area
        self.progress_label = QLabel("0/0 다운로드 중...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.download_list = QListWidget()

        main_layout.addWidget(self.progress_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.download_list)

        # Download type selector (MP3 / MP4)
        type_layout = QHBoxLayout()
        type_label = QLabel("다운로드 유형:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["MP3 (오디오)", "MP4 (영상)"])
        self.type_combo.setCurrentText("MP3 (오디오)")
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        main_layout.addLayout(type_layout)

        # Audio quality selector (visible when MP3 selected)
        self.audio_quality_widget = QWidget()
        self.audio_quality_layout = QHBoxLayout(self.audio_quality_widget)
        audio_quality_label = QLabel("음질:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["128kbps", "192kbps", "320kbps"])
        self.quality_combo.setCurrentText("192kbps")
        self.audio_quality_layout.addWidget(audio_quality_label)
        self.audio_quality_layout.addWidget(self.quality_combo)
        self.audio_quality_layout.addStretch()
        main_layout.addWidget(self.audio_quality_widget)

        # Default video quality selector (visible when MP4 selected)
        self.video_quality_widget = QWidget()
        self.video_quality_layout = QHBoxLayout(self.video_quality_widget)
        video_quality_label = QLabel("기본 화질:")
        self.video_quality_combo = QComboBox()
        self.video_quality_combo.addItems(["최대 화질", "2160p (4K)", "1440p (2K)", "1080p (FHD)", "720p (HD)", "480p", "360p"])
        self.video_quality_combo.setCurrentText("1080p (FHD)")
        self.video_quality_layout.addWidget(video_quality_label)
        self.video_quality_layout.addWidget(self.video_quality_combo)
        self.video_quality_layout.addStretch()
        self.video_quality_widget.setVisible(False)
        main_layout.addWidget(self.video_quality_widget)

        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_button = QPushButton("폴더 선택")
        self.folder_button.clicked.connect(self.select_folder)
        self.folder_label = QLabel("폴더가 선택되지 않았습니다")

        folder_layout.addWidget(self.folder_button)
        folder_layout.addWidget(self.folder_label)

        main_layout.addLayout(folder_layout)

        # Download button
        self.download_button = QPushButton("다운로드")
        self.download_button.clicked.connect(self.start_download)

        main_layout.addWidget(self.download_button)

        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Download state tracking
        self.download_items = {}       # Maps URL to list item index
        self._current_download_index = 0  # Index of currently downloading item
        self._is_downloading = False    # Guard against concurrent downloads
        self._video_info = []           # Stores resolution check results

        # Restore last saved folder path
        saved_folder = get_saved_folder()
        if saved_folder:
            self.folder_label.setText(saved_folder)

    def on_type_changed(self, text):
        """Toggle visibility of audio/video quality selectors."""
        is_mp3 = "MP3" in text
        self.audio_quality_widget.setVisible(is_mp3)
        self.video_quality_widget.setVisible(not is_mp3)

    def check_resolutions(self):
        """Fetch resolution info for each URL."""
        urls = self.url_textedit.toPlainText().strip()
        if not urls:
            QMessageBox.warning(self, "입력 오류",
                                "최소 하나의 유튜브 URL을 입력하세요.")
            return

        url_list = [u.strip() for u in urls.split('\n') if u.strip()]
        if not url_list:
            QMessageBox.warning(self, "입력 오류",
                                "유효한 유튜브 URL을 입력하세요.")
            return

        self.info_table.setRowCount(len(url_list))
        for i in range(len(url_list)):
            self.info_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.info_table.setItem(i, 1, QTableWidgetItem("조회 중..."))
            self.info_table.setItem(i, 2, QTableWidgetItem("..."))
            combo = QComboBox()
            combo.addItem("조회 중...")
            self.info_table.setCellWidget(i, 3, combo)

        self.info_table.setVisible(True)
        self.update_status("화질 정보 조회 중...")

        worker = ResolutionCheckWorker(url_list)
        worker.finished.connect(self.on_resolution_check_finished)
        worker.error.connect(self.on_resolution_check_error)
        worker.start()
        worker.wait()  # Wait for completion (blocking is OK for small batches)

    def on_resolution_check_finished(self, results):
        """Populate the info table with resolution data."""
        for i, info in enumerate(results):
            if i >= self.info_table.rowCount():
                break
            title_item = self.info_table.item(i, 1)
            if title_item:
                title_item.setText(info['title'])

            res_item = self.info_table.item(i, 2)
            if res_item:
                if info['resolutions']:
                    res_text = ", ".join(f"{h}p" for h in info['resolutions'][:10])
                    if len(info['resolutions']) > 10:
                        res_text += f" (+{len(info['resolutions']) - 10} more)"
                    res_item.setText(res_text)
                else:
                    res_item.setText("사용 불가")

            combo = self.info_table.cellWidget(i, 3)
            if combo and info['resolutions']:
                combo.clear()
                for h in info['resolutions']:
                    combo.addItem(f"{h}p")
                # Default to highest resolution
                combo.setCurrentIndex(0)

        self._video_info = results
        self.update_status("화질 정보 조회 완료")

    def on_resolution_check_error(self, url, error):
        """Handle resolution check errors."""
        self.update_status(f"화질 조회 오류: {error}")

    def update_status(self, message: str) -> None:
        """Update the status bar with a message."""
        self.status_bar.showMessage(message)

    def update_progress_label(self, current_index: int, total: int,
                              title: str) -> None:
        """Update progress label and track current download index."""
        self._current_download_index = current_index - 1  # 0-based
        self.progress_label.setText(
            f"{current_index}/{total} 다운로드 중... - {title}"
        )

    def show_error(self, url: str, error_message: str) -> None:
        """Display error in status bar."""
        self.update_status(f"오류 발생: {error_message}")

    def update_download_progress(self, title: str, percentage: float) -> None:
        """Update progress for the current download item and progress bar."""
        item_index = self._current_download_index
        list_item = self.download_list.item(item_index)
        if list_item:
            if percentage < 100:
                list_item.setText(f"⬇️ 다운로드 중 {int(percentage)}%")
            else:
                list_item.setText("✅ 완료")
        self.progress_bar.setValue(int(percentage))

    def mark_download_completed(self, filename: str) -> None:
        """Mark the current download as completed."""
        item_index = self._current_download_index
        list_item = self.download_list.item(item_index)
        if list_item:
            list_item.setText(f"✅ 완료 - {filename}")
        self.progress_bar.setValue(100)

    def mark_download_error(self, url: str, error_message: str) -> None:
        """Mark the current download as failed with error message."""
        item_index = self._current_download_index
        list_item = self.download_list.item(item_index)
        if list_item:
            # Truncate long error messages for display
            display_msg = error_message if len(error_message) <= 80 else error_message[:77] + "..."
            list_item.setText(f"❌ {display_msg}")

    def set_download_ui_enabled(self, enabled: bool) -> None:
        """Enable or disable UI controls during download."""
        self.url_textedit.setEnabled(enabled)
        self.check_button.setEnabled(enabled)
        self.type_combo.setEnabled(enabled)
        self.quality_combo.setEnabled(enabled)
        self.video_quality_combo.setEnabled(enabled)
        self.folder_button.setEnabled(enabled)
        self.download_button.setEnabled(enabled)
        self.download_button.setText("다운로드" if enabled else "다운로드 중...")

        # Disable table combo boxes during download
        for row in range(self.info_table.rowCount()):
            combo = self.info_table.cellWidget(row, 3)
            if combo:
                combo.setEnabled(enabled)

    def select_folder(self) -> None:
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, "출력 폴더 선택"
        )
        if folder:
            self.folder_label.setText(folder)
            save_folder(folder)

    def get_selected_resolutions(self) -> list:
        """Get the selected resolution for each video from the table."""
        resolutions = []
        for row in range(self.info_table.rowCount()):
            combo = self.info_table.cellWidget(row, 3)
            if combo:
                text = combo.currentText()
                # Extract height number (e.g., "1080p" -> 1080)
                height = int(text.replace('p', '')) if text.replace('p', '').isdigit() else 0
                resolutions.append(height)
            else:
                resolutions.append(0)
        return resolutions

    def closeEvent(self, event) -> None:
        """Handle window close with download-in-progress check."""
        if self._is_downloading:
            reply = QMessageBox.question(
                self, "다운로드 중단 확인",
                "다운로드가 진행 중입니다.\n정말 종료하시겠습니까?",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        event.accept()

    def start_download(self) -> None:
        """Validate inputs and start download process.

        Overridden by main.py to wire DownloadWorker signals.
        This stub provides basic validation feedback.
        """
        urls = self.url_textedit.toPlainText().strip()

        if not urls:
            QMessageBox.warning(self, "입력 오류",
                                "최소 하나의 유튜브 URL을 입력하세요.")
            return

        url_list = [u.strip() for u in urls.split('\n') if u.strip()]

        if not url_list:
            QMessageBox.warning(self, "입력 오류",
                                "유효한 유튜브 URL을 입력하세요.")
            return

        folder_path = self.folder_label.text()
        if folder_path == "폴더가 선택되지 않았습니다":
            QMessageBox.warning(self, "입력 오류",
                                "출력 폴더를 선택하세요.")
            return
