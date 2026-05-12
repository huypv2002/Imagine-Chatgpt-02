"""
Auto-Updater — Check GitHub Releases for new versions and update app.
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
from pathlib import Path

from PySide6.QtCore import QThread, Signal

# ============================================================
# CONFIG
# ============================================================
GITHUB_OWNER = "huypv2002"
GITHUB_REPO = "Imagine-Chatgpt-02"
ASSET_NAME = "Imagine-GPT-windows.zip"
EXE_NAME = "Imagine-GPT.exe"
# ============================================================


def runtime_app_dir() -> Path:
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        return Path(sys.executable).resolve().parent
    return Path(__file__).parent


VERSION_FILE = runtime_app_dir() / "VERSION"


def get_current_version() -> str:
    try:
        return VERSION_FILE.read_text().strip()
    except Exception:
        return "0.0"


class UpdateChecker(QThread):
    """Check GitHub for new release"""
    result = Signal(bool, str, str, str, str)  # has_update, tag, download_url, notes, error

    def run(self):
        try:
            from curl_cffi import requests as cffi_requests
            url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
            resp = cffi_requests.get(url, timeout=15, impersonate="chrome")
            if resp.status_code != 200:
                self.result.emit(False, "", "", "", f"HTTP {resp.status_code}")
                return

            data = resp.json()
            tag = data.get("tag_name", "")
            notes = data.get("body", "")

            # Compare versions
            remote_ver = tag.lstrip("v")
            local_ver = get_current_version()

            if remote_ver <= local_ver:
                self.result.emit(False, tag, "", notes, "")
                return

            # Find asset
            download_url = ""
            for asset in data.get("assets", []):
                if asset.get("name") == ASSET_NAME:
                    download_url = asset.get("browser_download_url", "")
                    break

            if not download_url:
                self.result.emit(False, tag, "", notes, "Không tìm thấy file update")
                return

            self.result.emit(True, tag, download_url, notes, "")

        except Exception as e:
            self.result.emit(False, "", "", "", str(e))


class UpdateDownloader(QThread):
    """Download and extract update"""
    progress = Signal(int)  # percent
    finished = Signal(bool, str)  # success, path_or_error

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            from curl_cffi import requests as cffi_requests

            # Download
            tmp_dir = Path(tempfile.gettempdir()) / "_imagine_update"
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            tmp_dir.mkdir(parents=True)

            zip_path = tmp_dir / ASSET_NAME

            resp = cffi_requests.get(self.url, timeout=300, impersonate="chrome", stream=True)
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            self.progress.emit(int(downloaded / total * 100))

            # Extract
            extract_dir = tmp_dir / "extracted"
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            # Find app folder (folder containing EXE)
            app_dir = None
            for p in extract_dir.rglob(EXE_NAME):
                app_dir = p.parent
                break

            if not app_dir:
                # Maybe EXE is in root
                app_dir = extract_dir

            self.finished.emit(True, str(app_dir))

        except Exception as e:
            self.finished.emit(False, str(e))


def apply_update(new_app_dir: str):
    """Create batch script to replace app files and restart"""
    import subprocess

    app_dir = runtime_app_dir()
    bat_path = app_dir / "_updater.bat"

    # Batch script: wait for process to exit, copy new files, restart
    script = f'''@echo off
echo Updating Imagine-GPT...
timeout /t 3 /nobreak >nul

REM Delete old files (preserve data/ and output/)
for /d %%i in ("{app_dir}\\*") do (
    if /i not "%%~nxi"=="data" if /i not "%%~nxi"=="output" if /i not "%%~nxi"=="_update_tmp" (
        rmdir /s /q "%%i"
    )
)
for %%i in ("{app_dir}\\*") do (
    if /i not "%%~nxi"=="_updater.bat" (
        del /f /q "%%i"
    )
)

REM Copy new files
xcopy /s /e /y "{new_app_dir}\\*" "{app_dir}\\" >nul

REM Start new version
start "" "{app_dir}\\{EXE_NAME}"

REM Cleanup
timeout /t 2 /nobreak >nul
del "%~f0"
'''

    bat_path.write_text(script, encoding="utf-8")

    # Launch batch and exit
    CREATE_NEW_CONSOLE = 0x00000010
    subprocess.Popen(
        ["cmd", "/c", str(bat_path)],
        creationflags=CREATE_NEW_CONSOLE,
        close_fds=True
    )
    os._exit(0)
