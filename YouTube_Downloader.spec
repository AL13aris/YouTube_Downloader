# -*- mode: python ; coding: utf-8 -*-
import os
import shutil
import inspect

block_cipher = None

# ── ffmpeg/ffprobe 자동 탐지 ──
# 빌드 시 프로젝트 디렉토리 → Chocolatey → 시스템 PATH 순으로 검색
def find_ffmpeg_binaries():
    """Find ffmpeg.exe and ffprobe.exe for bundling."""
    # spec 파일 기준 프로젝트 디렉토리
    spec_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    search_paths = [
        # 프로젝트 디렉토리 (로컬 개발 시)
        spec_dir,
        # Chocolatey 설치 경로
        r'C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin',
        r'C:\ProgramData\chocolatey\lib\ffmpeg.portable\tools\ffmpeg\bin',
        # 시스템 PATH에서 검색
    ]

    ffmpeg_path = None
    ffprobe_path = None

    # 명시적 경로에서 먼저 검색
    for sp in search_paths:
        if ffmpeg_path and ffprobe_path:
            break
        if not os.path.isdir(sp):
            continue
        if ffmpeg_path is None and os.path.exists(os.path.join(sp, 'ffmpeg.exe')):
            ffmpeg_path = os.path.join(sp, 'ffmpeg.exe')
        if ffprobe_path is None and os.path.exists(os.path.join(sp, 'ffprobe.exe')):
            ffprobe_path = os.path.join(sp, 'ffprobe.exe')

    # 시스템 PATH에서 검색
    if ffmpeg_path is None:
        ffmpeg_path = shutil.which('ffmpeg')
    if ffprobe_path is None:
        ffprobe_path = shutil.which('ffprobe')

    if ffmpeg_path and ffprobe_path:
        print(f'[BUILD] ffmpeg found: {os.path.dirname(ffmpeg_path)}')
        return [
            (ffmpeg_path, '.'),
            (ffprobe_path, '.'),
        ]

    print('[BUILD] WARNING: ffmpeg/ffprobe not found. '
          'Place ffmpeg.exe and ffprobe.exe in the output folder alongside the exe.')
    return []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=find_ffmpeg_binaries(),
    datas=[],
    hiddenimports=[
        'yt_dlp',
        'yt_dlp.extractor',
        'yt_dlp.postprocessor',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='YouTube_Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# --onedir mode: collect all files into a directory
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='YouTube_Downloader',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
