# 유튜브 MP3/MP4 추출기

PyQt6 기반 데스크톱 애플리케이션으로, YouTube 동영상에서 MP3 오디오 또는 MP4 비디오를 다운로드합니다.

**중요:** [Releases] 페이지에서 배포용 실행 파일을 다운로드하시면, **별도의 ffmpeg 설치 없이 바로 사용**하실 수 있습니다.

## 주요 기능

- **MP3 오디오 추출** - YouTube 동영상에서 고음질 MP3 파일 추출 (128/192/320kbps)
- **MP4 비디오 다운로드** - 선택한 화질로 동영상 다운로드 (최대 화질 / 4K / 2K / 1080p / 720p / 480p / 360p)
- **배치 다운로드** - 여러 URL을 한 번에 입력하고 순차적으로 다운로드
- **실시간 진행률 표시** - 개별 다운로드 및 전체 진행 상황 확인
- **화질 사전 확인** - 다운로드 전 각 영상의 지원 화질 확인
- **ffmpeg 자동 감지** - 시스템 또는 Chocolatey에 설치된 ffmpeg 자동 탐지

## 시스템 요구 사항

### 1. 일반 사용자 (릴리즈 버전 실행 시)
- Windows 10/11 (추가 설치 요소 없음)

### 2. 개발자 (소스 코드에서 직접 실행/빌드 시)
- ffmpeg (자동 감지되지 않을 경우 [ffmpeg.org](https://ffmpeg.org/download.html)에서 설치)

## 실행 방법

### 방법 1. 실행 파일 사용 (일반 사용자 권장)

1. 본 레포지토리 우측의 **Releases** 메뉴에서 최신 버전의 `YouTube_Downloader.zip`을 다운로드합니다.
2. 압축을 해제한 후, **`YouTube_Downloader.exe`**를 더블 클릭하여 실행합니다.
*(이 패키지에는 ffmpeg가 내장되어 있어 별도의 설치가 필요하지 않습니다.)*


### 방법 2. 소스 코드에서 실행 (개발자용)

```bash
pip install -r requirements.txt
python main.py
```

## 사용 방법

1. **URL 입력** - YouTube URL을 한 줄에 하나씩 입력 (여러 개 가능)
2. **화질 확인** - "화질 확인" 버튼을 클릭하여 각 영상의 지원 화질 확인 (선택 사항)
3. **다운로드 유형 선택** - MP3 또는 MP4 선택
4. **품질 설정**
   - MP3 선택 시: 음질 선택 (128/192/320kbps)
   - MP4 선택 시: 기본 화질 선택 (개별 화질 선택이 없을 때 적용)
5. **폴더 선택** - 다운로드 저장 위치 지정
6. **다운로드** - "다운로드" 버튼 클릭

## 빌드 방법

### 1. Python 환경 설정

Python 3.10 이상이 설치되어 있는지 확인합니다.
현재 빌드는 3.13 에서 빌드 하였습니다.

```bash
python --version
```

Python이 설치되어 있지 않다면 [python.org](https://www.python.org/downloads/)에서 다운로드하여 설치하세요.

### 2. 의존성 설치

프로젝트 폴더로 이동한 후 필요한 패키지를 설치합니다.

```bash
cd YouTube_Downloader
pip install -r requirements.txt
pip install pyinstaller
```

설치되는 주요 패키지:
- `PyQt6` - GUI 프레임워크
- `yt-dlp` - YouTube 다운로드 엔진
- `pyinstaller` - 실행 파일 빌드 도구

### 3. ffmpeg 설치

ffmpeg는 오디오/비디오 처리에 필수적입니다. 다음 방법 중 하나로 설치하세요.

**Chocolatey 사용 (권장):**
```powershell
choco install ffmpeg
```

**Scoop 사용:**
```powershell
scoop install ffmpeg
```

**수동 설치:**
1. [ffmpeg.org](https://ffmpeg.org/download.html)에서 Windows 빌드 다운로드
2. 압축 해제 후 `ffmpeg.exe`가 있는 `bin` 폴더 경로 확인
3. 시스템 환경 변수의 `Path`에 추가

설치 확인:
```bash
ffmpeg -version
```

### 4. 빌드 실행

```bash
pyinstaller --clean --noconfirm YouTube_Downloader.spec
```

빌드 옵션 설명:
- `--clean` - 이전 빌드 캐시 삭제 후 새 빌드
- `--noconfirm` - 기존 출력 폴더 덮어쓰기 확인 없이 진행

빌드된 파일은 `dist/YouTube_Downloader/` 폴더에 생성됩니다.

### 5. 빌드 결과 확인

```
dist/
└── YouTube_Downloader/
    ├── YouTube_Downloader.exe   # 실행 파일
    ├── (dll, 라이브러리 파일들...)
    └── ...
```

`YouTube_Downloader.exe`를 더블 클릭하여 실행합니다.

### 6. 소스 코드에서 직접 실행 (테스트용)

빌드 없이 바로 테스트하려면:

```bash
python main.py
```

## 프로젝트 구조

```
├── main.py                      # 애플리케이션 진입점
├── downloader.py                # 다운로드 워커 (백그라운드 스레드)
├── ui_mainwindow.py             # PyQt6 UI
├── utils.py                     # 유틸리티 (의존성 확인, 파일명 처리 등)
├── requirements.txt             # Python 의존성
├── YouTube_Downloader.spec   # PyInstaller 빌드 설정
└── dist/                        # 빌드 출력 폴더
```

## 기술 스택

- **GUI**: PyQt6
- **다운로드 엔진**: yt-dlp
- **오디오/비디오 처리**: ffmpeg
- **빌드 도구**: PyInstaller

## 라이선스

이 프로젝트는 **GNU GPL v3** 라이선스 하에 배포됩니다.

PyQt6이 GPL v3 라이선스를 사용하므로, 이를 의존하는 본 프로젝트 역시 GPL v3를 따릅니다.

### 제3자 라이선스

| 라이브러리 | 라이선스 |
|---|---|
| PyQt6 | GPL v3 |
| yt-dlp | The Unlicense |
| ffmpeg | LGPL v2.1+ |
| PyInstaller | GPL v2+ (special exception) |

### 배포 시 주의 사항

- 이 프로그램을 재배포할 경우 소스 코드도 함께 공개해야 합니다.
- ffmpeg 사용에 따라 ffmpeg의 소스 코드 또는 라이선스 정보를 제공해야 합니다.
- 상업적 목적으로 재배포하려면 PyQt6 상업 라이선스를 구매해야 합니다.

전체 GPL v3 라이선스 텍스트: [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html)
