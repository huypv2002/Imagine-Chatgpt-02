#!/usr/bin/env python3
"""
Text-to-Image Generator — 2-Panel Layout
PySide6 | Light theme xám nhạt | Session management | Grid-based
"""

import json
import sys
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox, QProgressBar,
    QStackedWidget, QFileDialog, QMessageBox, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QScrollArea,
    QSplitter, QLineEdit, QDialog, QDialogButtonBox, QInputDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QRectF, QUrl
from PySide6.QtGui import (
    QColor, QLinearGradient, QRadialGradient, QDesktopServices,
    QPainter, QBrush, QPen, QPainterPath
)

from services.account_service import account_service
from services.openai_backend_api import OpenAIBackendAPI, InvalidAccessTokenError
from utils.log import logger


# ═══════════════════════════════════════════════════════════════════════════════
# LOCAL NAMES STORAGE
# ═══════════════════════════════════════════════════════════════════════════════

NAMES_FILE = Path(__file__).parent / "data" / "account_names.json"


def _load_names() -> dict:
    if NAMES_FILE.exists():
        try:
            return json.loads(NAMES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_names(names: dict):
    NAMES_FILE.parent.mkdir(parents=True, exist_ok=True)
    NAMES_FILE.write_text(json.dumps(names, ensure_ascii=False, indent=2), encoding="utf-8")


def get_account_name(token: str) -> str:
    return _load_names().get(token, "")


def set_account_name(token: str, name: str):
    names = _load_names()
    if name.strip():
        names[token] = name.strip()
    else:
        names.pop(token, None)
    _save_names(names)


# ═══════════════════════════════════════════════════════════════════════════════
# STYLESHEET
# ═══════════════════════════════════════════════════════════════════════════════

STYLESHEET = """
* { margin: 0; padding: 0; }
QMainWindow { background-color: #f0f2f5; }
QWidget { background-color: transparent; color: #1a1a2e; font-family: "Inter", -apple-system, "Segoe UI", sans-serif; font-size: 13px; }

/* Panels */
QFrame#leftPanel { background: #ffffff; border-right: 1px solid #e2e4e9; }
QFrame#rightPanel { background: #f8f9fb; }

/* Section title */
QLabel#sectionTitle { color: #1a1a2e; font-size: 13px; font-weight: 700; padding: 2px 0; }
QLabel#fieldLabel { color: #4b5563; font-size: 12px; font-weight: 500; }
QLabel#mutedLabel { color: #9ca3af; font-size: 11px; }
QLabel#statusOk { color: #059669; font-size: 12px; font-weight: 600; }
QLabel#statusErr { color: #dc2626; font-size: 12px; font-weight: 600; }

/* Buttons */
QPushButton#primaryBtn { background-color: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; font-size: 12px; min-height: 32px; min-width: 70px; }
QPushButton#primaryBtn:hover { background-color: #1d4ed8; }
QPushButton#primaryBtn:disabled { background-color: #93c5fd; color: #fff; }

QPushButton#ghostBtn { background-color: #ffffff; color: #374151; border: 1px solid #d1d5db; border-radius: 6px; padding: 7px 14px; font-weight: 500; font-size: 12px; min-height: 32px; min-width: 60px; }
QPushButton#ghostBtn:hover { background-color: #f3f4f6; border-color: #9ca3af; }
QPushButton#ghostBtn:disabled { background-color: #f9fafb; color: #9ca3af; border-color: #e5e7eb; }

QPushButton#dangerBtn { background-color: #ffffff; color: #dc2626; border: 1px solid #fca5a5; border-radius: 6px; padding: 7px 14px; font-weight: 500; font-size: 12px; min-height: 32px; min-width: 60px; }
QPushButton#dangerBtn:hover { background-color: #fef2f2; }

QPushButton#successBtn { background-color: #059669; color: #fff; border: none; border-radius: 6px; padding: 7px 14px; font-weight: 500; font-size: 12px; min-height: 32px; min-width: 60px; }
QPushButton#successBtn:hover { background-color: #047857; }

QPushButton#linkBtn { background: transparent; color: #2563eb; border: none; padding: 4px 8px; font-size: 12px; font-weight: 500; text-decoration: underline; }
QPushButton#linkBtn:hover { color: #1d4ed8; }

/* Inputs */
QLineEdit, QTextEdit { background-color: #fff; border: 1.5px solid #d1d5db; border-radius: 6px; padding: 8px 10px; color: #1a1a2e; }
QLineEdit:focus, QTextEdit:focus { border: 1.5px solid #2563eb; }
QComboBox { background-color: #fff; border: 1.5px solid #d1d5db; border-radius: 6px; padding: 7px 10px; color: #1a1a2e; min-height: 32px; }
QComboBox:hover { border-color: #6b7280; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #6b7280; margin-right: 8px; }
QComboBox QAbstractItemView { background-color: #fff; border: 1px solid #d1d5db; border-radius: 6px; padding: 4px; selection-background-color: #eff6ff; outline: none; }

/* Table */
QTableWidget { background-color: #fff; border: 1.5px solid #e2e4e9; border-radius: 8px; gridline-color: #f0f1f3; }
QTableWidget::item { padding: 8px 10px; border-bottom: 1px solid #f0f1f3; color: #374151; font-size: 12px; }
QTableWidget::item:selected { background-color: #eff6ff; color: #1a1a2e; }
QHeaderView::section { background-color: #f4f5f7; color: #4b5563; padding: 8px 10px; border: none; border-bottom: 1.5px solid #e2e4e9; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }

/* Progress */
QProgressBar { background: #e5e7eb; border: none; border-radius: 3px; height: 6px; color: transparent; }
QProgressBar::chunk { background: #2563eb; border-radius: 3px; }

/* Scrollbar */
QScrollBar:vertical { background: transparent; width: 6px; }
QScrollBar::handle:vertical { background: #d1d5db; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #9ca3af; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { height: 0; }
QScrollArea { background: transparent; border: none; }
"""


# ═══════════════════════════════════════════════════════════════════════════════
# WORKERS
# ═══════════════════════════════════════════════════════════════════════════════

class RefreshWorker(QThread):
    finished = Signal(dict)
    def __init__(self, tokens):
        super().__init__()
        self.tokens = tokens
    def run(self):
        self.finished.emit(account_service.refresh_accounts(self.tokens))


class ImageWorker(QThread):
    progress = Signal(int, int, str)
    item_done = Signal(int, dict)
    finished = Signal(list)

    CONCURRENCY = 3  # Số luồng song song

    def __init__(self, prompts, model, output_dir, ratio="16:9"):
        super().__init__()
        self.prompts = prompts
        self.model = model
        self.output_dir = output_dir
        self.ratio = ratio
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed

        total = len(self.prompts)
        results = [None] * total
        lock = threading.Lock()
        done_count = [0]

        def do_one(idx):
            if not self._running:
                return idx, {"success": False, "prompt": self.prompts[idx], "error": "Đã dừng"}
            prompt = self.prompts[idx]
            self.progress.emit(idx + 1, total, prompt[:50])
            try:
                token = account_service.get_available_access_token()
                result = self._gen(token, prompt, idx)
                account_service.mark_image_result(token, result["success"])
                return idx, result
            except Exception as e:
                return idx, {"success": False, "prompt": prompt, "error": str(e)}

        # Pipeline: submit CONCURRENCY tasks, khi 1 xong thì submit tiếp
        workers = min(self.CONCURRENCY, total)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # Submit initial batch
            pending = {}
            next_idx = 0

            # Fill initial slots
            for _ in range(min(workers, total)):
                if next_idx < total:
                    f = pool.submit(do_one, next_idx)
                    pending[f] = next_idx
                    next_idx += 1

            while pending:
                if not self._running:
                    for f in pending:
                        f.cancel()
                    break

                # Wait for any one to complete
                done_futures = [f for f in pending if f.done()]
                if not done_futures:
                    # Brief sleep to avoid busy loop
                    import time
                    time.sleep(0.1)
                    continue

                for f in done_futures:
                    idx, result = f.result()
                    results[idx] = result
                    self.item_done.emit(idx, result)

                    with lock:
                        done_count[0] += 1

                    del pending[f]

                    # Submit next task if available
                    if next_idx < total and self._running:
                        nf = pool.submit(do_one, next_idx)
                        pending[nf] = next_idx
                        next_idx += 1

        # Fill cancelled
        for i in range(total):
            if results[i] is None:
                results[i] = {"success": False, "prompt": self.prompts[i], "error": "Đã dừng"}

        self.finished.emit(results)

    def _gen(self, token, prompt, idx=0):
        try:
            api = OpenAIBackendAPI(access_token=token)
            conv_id = None
            file_ids, sediment_ids = [], []

            # Wrap prompt với ratio instruction
            RATIO_MAP = {
                "1:1": "square 1:1",
                "16:9": "16:9 landscape wide",
                "9:16": "9:16 portrait vertical",
                "4:3": "4:3 landscape",
                "3:4": "3:4 portrait",
                "3:2": "3:2 landscape",
                "2:3": "2:3 portrait",
            }
            ratio_desc = RATIO_MAP.get(self.ratio, self.ratio)
            full_prompt = f"Create image ratio {ratio_desc} with this prompt: {prompt}"

            # Xác định folder lưu theo tên file txt
            prompt_files = getattr(self, 'prompt_files', None)
            if prompt_files and idx < len(prompt_files):
                folder_name = prompt_files[idx]
            else:
                folder_name = "output"
            save_dir = self.output_dir / folder_name
            save_dir.mkdir(parents=True, exist_ok=True)

            # Tính STT trong folder này
            # Đếm số file .png đã có trong folder + 1
            existing = len(list(save_dir.glob("*.png")))
            img_number = existing + 1

            for ev in api.stream_conversation(prompt=full_prompt, model=self.model, system_hints=["picture_v2"]):
                try:
                    data = json.loads(ev) if isinstance(ev, str) else ev
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue
                if not isinstance(data, dict):
                    continue
                if "conversation_id" in data:
                    conv_id = data["conversation_id"]
                msg = data.get("message")
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content")
                if not isinstance(content, dict):
                    continue
                if content.get("content_type") == "multimodal_text":
                    for part in content.get("parts", []):
                        if isinstance(part, dict) and "asset_pointer" in part:
                            ptr = part["asset_pointer"]
                            if ptr.startswith("file-service://"):
                                fid = ptr[len("file-service://"):]
                                if fid not in file_ids:
                                    file_ids.append(fid)
                            elif ptr.startswith("sediment://"):
                                sid = ptr[len("sediment://"):]
                                if sid not in sediment_ids:
                                    sediment_ids.append(sid)
            if conv_id:
                urls = api.resolve_conversation_image_urls(
                    conversation_id=conv_id, file_ids=file_ids,
                    sediment_ids=sediment_ids, poll=True)
                if urls:
                    imgs = api.download_image_bytes(urls)
                    saved = []
                    for i, d in enumerate(imgs):
                        # Tên file: STT.png (hoặc STT_1.png nếu nhiều ảnh/prompt)
                        if len(imgs) == 1:
                            fname = f"{img_number}.png"
                        else:
                            fname = f"{img_number}_{i+1}.png"
                        fp = save_dir / fname
                        fp.write_bytes(d)
                        saved.append(str(fp))
                    # Delete conversation
                    try:
                        path = f"/backend-api/conversation/{conv_id}"
                        api.session.patch(api.base_url + path,
                            headers=api._headers(path, {"Content-Type": "application/json"}),
                            json={"is_visible": False}, timeout=15)
                    except Exception:
                        pass
                    return {"success": True, "prompt": prompt, "files": saved}
            return {"success": False, "prompt": prompt, "error": "Không tạo được ảnh"}
        except Exception as e:
            return {"success": False, "prompt": prompt, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# LEFT PANEL — Settings + Session + Batch
# ═══════════════════════════════════════════════════════════════════════════════

class LeftPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("leftPanel")
        self.setFixedWidth(320)
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(16)
        lay.setContentsMargins(16, 16, 16, 16)

        # ─── Thiết lập
        lay.addWidget(self._title("Thiết lập"))

        # Model
        lay.addWidget(self._field("Model"))
        self.model_cb = QComboBox()
        self.model_cb.addItems(["gpt-image-2", "codex-gpt-image-2"])
        lay.addWidget(self.model_cb)

        # Tỉ lệ
        lay.addWidget(self._field("Tỉ lệ ảnh"))
        self.ratio_cb = QComboBox()
        self.ratio_cb.addItems(["16:9", "1:1", "9:16", "4:3", "3:4", "3:2", "2:3"])
        lay.addWidget(self.ratio_cb)

        # Số luồng / account
        lay.addWidget(self._field("Luồng / account (max 3)"))
        self.threads_cb = QComboBox()
        self.threads_cb.addItems(["1", "2", "3"])
        self.threads_cb.setCurrentIndex(0)  # Mặc định 1
        lay.addWidget(self.threads_cb)

        # ─── Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background: #e5e7eb; max-height: 1px;")
        lay.addWidget(sep2)

        # ─── Batch Job
        lay.addWidget(self._title("Batch Job"))

        # File prompt
        lay.addWidget(self._field("File prompt (.txt)"))
        fr = QHBoxLayout()
        fr.setSpacing(6)
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Chọn file .txt hoặc folder...")
        self.file_input.setReadOnly(True)
        fr.addWidget(self.file_input)
        btn_file = QPushButton("File")
        btn_file.setObjectName("ghostBtn")
        btn_file.setCursor(Qt.PointingHandCursor)
        btn_file.setFixedWidth(45)
        btn_file.clicked.connect(self._choose_file)
        fr.addWidget(btn_file)
        btn_dir = QPushButton("Folder")
        btn_dir.setObjectName("ghostBtn")
        btn_dir.setCursor(Qt.PointingHandCursor)
        btn_dir.setFixedWidth(55)
        btn_dir.clicked.connect(self._choose_prompt_folder)
        fr.addWidget(btn_dir)
        lay.addLayout(fr)

        # Folder lưu
        lay.addWidget(self._field("Thư mục lưu"))
        fr2 = QHBoxLayout()
        fr2.setSpacing(6)
        self.folder_input = QLineEdit()
        self.folder_input.setText(str(Path("./output").resolve()))
        self.folder_input.setReadOnly(True)
        fr2.addWidget(self.folder_input)
        btn_folder = QPushButton("...")
        btn_folder.setObjectName("ghostBtn")
        btn_folder.setCursor(Qt.PointingHandCursor)
        btn_folder.setFixedWidth(35)
        btn_folder.clicked.connect(self._choose_folder)
        fr2.addWidget(btn_folder)
        lay.addLayout(fr2)

        lay.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _title(self, text):
        l = QLabel(text)
        l.setObjectName("sectionTitle")
        return l

    def _field(self, text):
        l = QLabel(text)
        l.setObjectName("fieldLabel")
        return l

    def _choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file", "", "Text (*.txt);;Tất cả (*)")
        if path:
            self.file_input.setText(path)

    def _choose_prompt_folder(self):
        """Chọn folder chứa nhiều file .txt"""
        folder = QFileDialog.getExistingDirectory(self, "Chọn folder chứa file .txt")
        if folder:
            self.file_input.setText(folder)

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu")
        if folder:
            self.folder_input.setText(folder)


# ═══════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — Grid + Controls
# ═══════════════════════════════════════════════════════════════════════════════

class RightPanel(QFrame):
    PAGE_SIZE = 50

    def __init__(self, left_panel: LeftPanel, parent=None):
        super().__init__(parent)
        self.setObjectName("rightPanel")
        self.left = left_panel
        self.worker = None
        self._prompts = []
        self._statuses = []
        self._details = []
        self._current_page = 0
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.setContentsMargins(16, 16, 16, 16)

        # Header
        hdr = QHBoxLayout()
        hdr.setSpacing(8)
        self.page_label = QLabel("0 prompts")
        self.page_label.setObjectName("sectionTitle")
        hdr.addWidget(self.page_label)
        hdr.addStretch()
        self.status_label = QLabel("Chờ file TXT để bắt đầu")
        self.status_label.setObjectName("mutedLabel")
        hdr.addWidget(self.status_label)
        lay.addLayout(hdr)

        # Grid
        self.grid = QTableWidget()
        self.grid.setColumnCount(4)
        self.grid.setHorizontalHeaderLabels(["#", "Prompt", "Tiến độ", "Chi tiết"])
        h = self.grid.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Fixed)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        self.grid.setColumnWidth(0, 60)
        self.grid.setColumnWidth(2, 80)
        self.grid.verticalHeader().setVisible(False)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.grid.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.grid.cellDoubleClicked.connect(self._on_cell_click)
        lay.addWidget(self.grid)

        # Pagination
        pag = QHBoxLayout()
        pag.setSpacing(6)
        self.btn_prev = QPushButton("< Trước")
        self.btn_prev.setObjectName("ghostBtn")
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.clicked.connect(self._prev_page)
        self.btn_prev.setEnabled(False)
        pag.addWidget(self.btn_prev)
        self.page_info = QLabel("Trang 1/1")
        self.page_info.setObjectName("mutedLabel")
        self.page_info.setAlignment(Qt.AlignCenter)
        pag.addWidget(self.page_info)
        self.btn_next = QPushButton("Sau >")
        self.btn_next.setObjectName("ghostBtn")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.clicked.connect(self._next_page)
        self.btn_next.setEnabled(False)
        pag.addWidget(self.btn_next)
        pag.addStretch()
        lay.addLayout(pag)

        # Progress
        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        self.pbar.setTextVisible(False)
        self.pbar.setFixedHeight(6)
        lay.addWidget(self.pbar)

        # Bottom buttons
        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        self.btn_run = QPushButton("Chạy")
        self.btn_run.setStyleSheet("""
            QPushButton { background-color: #2563eb; color: #ffffff; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; font-size: 13px; min-height: 34px; }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #93c5fd; color: #ffffff; }
        """)
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.clicked.connect(self._run)
        bottom.addWidget(self.btn_run)
        self.btn_stop = QPushButton("Dừng")
        self.btn_stop.setObjectName("ghostBtn")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop)
        bottom.addWidget(self.btn_stop)
        self.btn_resume = QPushButton("Tiếp")
        self.btn_resume.setObjectName("ghostBtn")
        self.btn_resume.setCursor(Qt.PointingHandCursor)
        self.btn_resume.setEnabled(False)
        self.btn_resume.clicked.connect(self._resume)
        bottom.addWidget(self.btn_resume)
        btn_retry = QPushButton("Chạy lại lỗi")
        btn_retry.setObjectName("dangerBtn")
        btn_retry.setCursor(Qt.PointingHandCursor)
        btn_retry.clicked.connect(self._retry_failed)
        bottom.addWidget(btn_retry)
        btn_clear = QPushButton("Xóa prompt")
        btn_clear.setObjectName("ghostBtn")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(self._clear)
        bottom.addWidget(btn_clear)
        btn_open = QPushButton("Mở thư mục")
        btn_open.setObjectName("ghostBtn")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.clicked.connect(self._open_folder)
        bottom.addWidget(btn_open)
        bottom.addStretch()
        self.run_status = QLabel("")
        self.run_status.setObjectName("mutedLabel")
        bottom.addWidget(self.run_status)
        lay.addLayout(bottom)

    # ─── Pagination
    @property
    def _total_pages(self):
        return max(1, (len(self._prompts) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

    def _refresh_grid_page(self):
        start = self._current_page * self.PAGE_SIZE
        end = min(start + self.PAGE_SIZE, len(self._prompts))
        page_items = self._prompts[start:end]
        self.grid.setRowCount(len(page_items))
        for i, p in enumerate(page_items):
            real_idx = start + i
            num = QTableWidgetItem(str(real_idx + 1))
            num.setTextAlignment(Qt.AlignCenter)
            self.grid.setItem(i, 0, num)
            self.grid.setItem(i, 1, QTableWidgetItem(p))
            status = self._statuses[real_idx] if real_idx < len(self._statuses) else "Chờ"
            st = QTableWidgetItem(status)
            st.setTextAlignment(Qt.AlignCenter)
            if status == "OK":
                st.setForeground(QColor("#059669"))
            elif status == "Lỗi":
                st.setForeground(QColor("#dc2626"))
            elif "Đang" in status:
                st.setForeground(QColor("#2563eb"))
            else:
                st.setForeground(QColor("#9ca3af"))
            self.grid.setItem(i, 2, st)
            detail = self._details[real_idx] if real_idx < len(self._details) else ""
            det = QTableWidgetItem(detail)
            if status == "Lỗi":
                det.setForeground(QColor("#dc2626"))
            self.grid.setItem(i, 3, det)
        self.btn_prev.setEnabled(self._current_page > 0)
        self.btn_next.setEnabled(self._current_page < self._total_pages - 1)
        self.page_info.setText(f"Trang {self._current_page + 1}/{self._total_pages}")

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._refresh_grid_page()

    def _next_page(self):
        if self._current_page < self._total_pages - 1:
            self._current_page += 1
            self._refresh_grid_page()

    # ─── Load
    def load_prompts_from_file(self):
        path = self.left.file_input.text()
        if not path:
            return False
        p = Path(path)
        prompts = []
        # _prompt_files[i] = tên file txt gốc (không có .txt) cho prompt thứ i
        self._prompt_files = []

        if p.is_file():
            try:
                lines = [l.strip() for l in p.read_text(encoding="utf-8").split("\n") if l.strip()]
                prompts = lines
                file_name = p.stem  # tên file không có extension
                self._prompt_files = [file_name] * len(lines)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không đọc được file:\n{e}")
                return False
        elif p.is_dir():
            for tf in sorted(p.glob("*.txt")):
                try:
                    lines = [l.strip() for l in tf.read_text(encoding="utf-8").split("\n") if l.strip()]
                    prompts.extend(lines)
                    self._prompt_files.extend([tf.stem] * len(lines))
                except Exception:
                    pass
            if not prompts:
                QMessageBox.warning(self, "Trống", "Folder không có prompt hợp lệ.")
                return False
        else:
            return False

        self._prompts = prompts
        self._statuses = ["Chờ"] * len(prompts)
        self._details = [""] * len(prompts)
        self._current_page = 0
        self._refresh_grid_page()
        self.page_label.setText(f"{len(self._prompts)} prompts")
        self.status_label.setText("Sẵn sàng")
        return True

    # ─── Run
    def _run(self):
        if not self._prompts:
            if not self.load_prompts_from_file():
                return
        if not self._prompts:
            return
        accounts = account_service.list_accounts()
        if not accounts:
            QMessageBox.warning(self, "Chưa có session", "Thêm session token trước.")
            return
        self._statuses = ["Chờ"] * len(self._prompts)
        self._details = [""] * len(self._prompts)
        self._current_page = 0
        self._refresh_grid_page()
        out_dir = Path(self.left.folder_input.text())
        out_dir.mkdir(parents=True, exist_ok=True)
        model = self.left.model_cb.currentText()
        ratio = self.left.ratio_cb.currentText()
        # Tính tổng luồng = luồng/account * số accounts
        threads_per_acc = int(self.left.threads_cb.currentText())
        num_accounts = len(accounts)
        total_threads = min(threads_per_acc * num_accounts, 9)  # Cap tối đa 9
        self.worker = ImageWorker(self._prompts, model, out_dir, ratio)
        self.worker.CONCURRENCY = total_threads
        self.worker.prompt_files = getattr(self, '_prompt_files', ['output'] * len(self._prompts))
        self.worker.progress.connect(self._on_progress)
        self.worker.item_done.connect(self._on_item_done)
        self.worker.finished.connect(self._on_done)
        self.worker.start()
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_resume.setEnabled(False)
        self.pbar.setValue(0)
        self.run_status.setText("Đang chạy...")

    def _stop(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_resume.setEnabled(True)
        self.run_status.setText("Đã dừng")

    def _resume(self):
        start_idx = next((i for i, s in enumerate(self._statuses) if s == "Chờ"), None)
        if start_idx is None:
            QMessageBox.information(self, "Xong", "Tất cả prompts đã xử lý.")
            return
        accounts = account_service.list_accounts()
        if not accounts:
            QMessageBox.warning(self, "Chưa có session", "Thêm session token trước.")
            return
        remaining = self._prompts[start_idx:]
        out_dir = Path(self.left.folder_input.text())
        out_dir.mkdir(parents=True, exist_ok=True)
        model = self.left.model_cb.currentText()
        ratio = self.left.ratio_cb.currentText()
        threads_per_acc = int(self.left.threads_cb.currentText())
        num_accounts = len(accounts)
        total_threads = min(threads_per_acc * num_accounts, 9)
        self.worker = ImageWorker(remaining, model, out_dir, ratio)
        self.worker.CONCURRENCY = total_threads
        remaining_files = getattr(self, '_prompt_files', ['output'] * len(self._prompts))[start_idx:]
        self.worker.prompt_files = remaining_files
        self._resume_offset = start_idx
        self.worker.progress.connect(self._on_resume_progress)
        self.worker.item_done.connect(self._on_resume_item_done)
        self.worker.finished.connect(self._on_done)
        self.worker.start()
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_resume.setEnabled(False)
        self.run_status.setText("Đang tiếp tục...")

    # ─── Callbacks
    def _on_progress(self, cur, total, prompt):
        self.pbar.setValue(int(cur / total * 100))
        idx = cur - 1
        if idx < len(self._statuses):
            self._statuses[idx] = "Đang..."
            target_page = idx // self.PAGE_SIZE
            if target_page != self._current_page:
                self._current_page = target_page
            self._refresh_grid_page()
        self.run_status.setText(f"{cur}/{total}")

    def _on_item_done(self, idx, result):
        self._update_status(idx, result)

    def _on_resume_progress(self, cur, total, prompt):
        real_idx = self._resume_offset + cur - 1
        self.pbar.setValue(int((real_idx + 1) / len(self._prompts) * 100))
        if real_idx < len(self._statuses):
            self._statuses[real_idx] = "Đang..."
            target_page = real_idx // self.PAGE_SIZE
            if target_page != self._current_page:
                self._current_page = target_page
            self._refresh_grid_page()
        self.run_status.setText(f"{real_idx + 1}/{len(self._prompts)}")

    def _on_resume_item_done(self, idx, result):
        self._update_status(self._resume_offset + idx, result)

    def _update_status(self, idx, result):
        if idx >= len(self._statuses):
            return
        if result["success"]:
            self._statuses[idx] = "OK"
            files = result.get("files", [])
            self._details[idx] = Path(files[0]).name if files else ""
        else:
            self._statuses[idx] = "Lỗi"
            self._details[idx] = result.get("error", "")[:50]
        self._refresh_grid_page()

    def _on_done(self, results):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_resume.setEnabled(True)
        self.pbar.setValue(100)
        ok = sum(1 for s in self._statuses if s == "OK")
        fail = sum(1 for s in self._statuses if s == "Lỗi")
        self.run_status.setText(f"Xong: {ok} OK, {fail} lỗi")

    def _retry_failed(self):
        failed = [self._prompts[i] for i, s in enumerate(self._statuses) if s == "Lỗi"]
        if not failed:
            QMessageBox.information(self, "OK", "Không có prompt lỗi.")
            return
        self._prompts = failed
        self._statuses = ["Chờ"] * len(failed)
        self._details = [""] * len(failed)
        self._current_page = 0
        self._refresh_grid_page()
        self.page_label.setText(f"{len(failed)} prompts")
        self.run_status.setText(f"{len(failed)} lỗi → sẵn sàng chạy lại")

    def _clear(self):
        self._prompts = []
        self._statuses = []
        self._details = []
        self._current_page = 0
        self.grid.setRowCount(0)
        self.page_label.setText("0 prompts")
        self.status_label.setText("Chờ file TXT")
        self.pbar.setValue(0)
        self.run_status.setText("")
        self.page_info.setText("Trang 1/1")
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)

    def _open_folder(self):
        folder = Path(self.left.folder_input.text())
        folder.mkdir(parents=True, exist_ok=True)
        s = platform.system()
        try:
            if s == "Darwin":
                subprocess.run(["open", str(folder)])
            elif s == "Windows":
                subprocess.run(["explorer", str(folder)])
            else:
                subprocess.run(["xdg-open", str(folder)])
        except Exception:
            pass

    def _on_cell_click(self, row, col):
        """Double-click vào cột Chi tiết (3) → mở xem ảnh"""
        if col != 3:
            return
        item = self.grid.item(row, 3)
        if not item:
            return
        filename = item.text().strip()
        if not filename or not filename.endswith(".png"):
            return

        # Tìm file trong output folder
        out_dir = Path(self.left.folder_input.text())
        # Search in all subdirectories
        found = None
        for f in out_dir.rglob(filename):
            found = f
            break

        if not found or not found.exists():
            return

        # Hiện dialog xem ảnh
        from PySide6.QtGui import QPixmap
        dlg = QDialog(self)
        dlg.setWindowTitle(filename)
        dlg.setMinimumSize(600, 500)
        dl = QVBoxLayout(dlg)
        dl.setContentsMargins(10, 10, 10, 10)

        img_label = QLabel()
        pix = QPixmap(str(found))
        if not pix.isNull():
            # Scale to fit dialog
            scaled = pix.scaled(580, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(scaled)
        else:
            img_label.setText("Không thể hiển thị ảnh")
        img_label.setAlignment(Qt.AlignCenter)
        dl.addWidget(img_label)

        # Path info
        path_lbl = QLabel(str(found))
        path_lbl.setStyleSheet("color: #6b7280; font-size: 11px;")
        path_lbl.setWordWrap(True)
        dl.addWidget(path_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(dlg.accept)
        dl.addWidget(btns)
        dlg.exec()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self, max_sessions: int = 3):
        super().__init__()
        self.max_sessions = max_sessions
        self.setWindowTitle("Image Generator v1.0")
        self.setMinimumSize(1100, 680)
        self._build()

    def _build(self):
        central = QWidget()
        central.setStyleSheet("background: #f0f2f5;")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # macOS-style menu bar (dark)
        menu_bar = QWidget()
        menu_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a3a3c, stop:1 #2c2c2e);
                border-bottom: 1px solid #1c1c1e;
            }
        """)
        menu_bar.setFixedHeight(38)
        mb_lay = QHBoxLayout(menu_bar)
        mb_lay.setContentsMargins(80, 0, 12, 0)  # 80px left for macOS traffic lights
        mb_lay.setSpacing(2)

        # Segmented control (pill tabs)
        seg = QWidget()
        seg.setStyleSheet("""
            QWidget { background: rgba(255,255,255,0.08); border-radius: 6px; padding: 2px; }
        """)
        seg.setFixedHeight(28)
        seg_lay = QHBoxLayout(seg)
        seg_lay.setContentsMargins(3, 2, 3, 2)
        seg_lay.setSpacing(2)

        self.tab_gen = QPushButton("Tạo Ảnh")
        self.tab_gen.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.15);
                color: #fff;
                border: none;
                border-radius: 5px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background: rgba(255,255,255,0.2); }
        """)
        self.tab_gen.setCursor(Qt.PointingHandCursor)
        self.tab_gen.clicked.connect(lambda: self._switch(0))
        seg_lay.addWidget(self.tab_gen)

        self.tab_session = QPushButton("Quản Lý Session")
        self.tab_session.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255,255,255,0.6);
                border: none;
                border-radius: 5px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover { background: rgba(255,255,255,0.08); color: #fff; }
        """)
        self.tab_session.setCursor(Qt.PointingHandCursor)
        self.tab_session.clicked.connect(lambda: self._switch(1))
        seg_lay.addWidget(self.tab_session)

        mb_lay.addWidget(seg)
        mb_lay.addStretch()

        # App title
        title_lbl = QLabel("Image Generator")
        title_lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px; font-weight: 500; background: transparent; border: none;")
        mb_lay.addWidget(title_lbl)

        mb_lay.addStretch()

        # Liên hệ + Donate buttons
        btn_contact = QPushButton("Liên hệ")
        btn_contact.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255,255,255,0.6);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 5px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { color: #fff; border-color: rgba(255,255,255,0.3); }
        """)
        btn_contact.setCursor(Qt.PointingHandCursor)
        btn_contact.clicked.connect(self._show_zalo)
        mb_lay.addWidget(btn_contact)

        btn_donate = QPushButton("Donate")
        btn_donate.setStyleSheet("""
            QPushButton {
                background: rgba(251, 191, 36, 0.15);
                color: #fbbf24;
                border: 1px solid rgba(251, 191, 36, 0.3);
                border-radius: 5px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background: rgba(251, 191, 36, 0.25); }
        """)
        btn_donate.setCursor(Qt.PointingHandCursor)
        btn_donate.clicked.connect(self._show_donate)
        mb_lay.addWidget(btn_donate)

        root.addWidget(menu_bar)

        # Pages
        self.pages = QStackedWidget()

        # Page 0: Tạo Ảnh (left settings + right grid)
        gen_page = QWidget()
        gen_lay = QHBoxLayout(gen_page)
        gen_lay.setSpacing(0)
        gen_lay.setContentsMargins(0, 0, 0, 0)
        self.left_panel = LeftPanel()
        self.right_panel = RightPanel(self.left_panel)
        gen_lay.addWidget(self.left_panel)
        gen_lay.addWidget(self.right_panel)
        self.pages.addWidget(gen_page)

        # Page 1: Quản Lý Session (full width)
        self.session_page = SessionPage(max_sessions=self.max_sessions)
        self.pages.addWidget(self.session_page)

        root.addWidget(self.pages)

        # Connect file selection to auto-load grid
        self.left_panel.file_input.textChanged.connect(self._on_file_changed)

    def _switch(self, idx):
        self.pages.setCurrentIndex(idx)
        active_style = """
            QPushButton {
                background: rgba(255,255,255,0.15);
                color: #fff;
                border: none;
                border-radius: 5px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background: rgba(255,255,255,0.2); }
        """
        inactive_style = """
            QPushButton {
                background: transparent;
                color: rgba(255,255,255,0.6);
                border: none;
                border-radius: 5px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover { background: rgba(255,255,255,0.08); color: #fff; }
        """
        if idx == 0:
            self.tab_gen.setStyleSheet(active_style)
            self.tab_session.setStyleSheet(inactive_style)
        else:
            self.tab_gen.setStyleSheet(inactive_style)
            self.tab_session.setStyleSheet(active_style)
            self.session_page.reload()

    def _on_file_changed(self, path):
        if path and Path(path).exists():
            self.right_panel.load_prompts_from_file()

    def _show_zalo(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Liên hệ Admin")
        dlg.setMinimumSize(320, 400)
        dl = QVBoxLayout(dlg)
        dl.setSpacing(12)
        dl.setContentsMargins(20, 20, 20, 20)
        dl.addWidget(QLabel("Quét mã QR Zalo để liên hệ admin:"))
        from PySide6.QtGui import QPixmap
        img_label = QLabel()
        img_path = Path(__file__).parent / "zalo.jpg"
        if img_path.exists():
            pix = QPixmap(str(img_path))
            img_label.setPixmap(pix.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            img_label.setText(f"Chưa có file: assets/zalo.jpg")
            img_label.setStyleSheet("color: #9ca3af;")
        img_label.setAlignment(Qt.AlignCenter)
        dl.addWidget(img_label)
        dl.addWidget(QLabel("Nâng cấp thêm account, hỗ trợ kỹ thuật."))
        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(dlg.accept)
        dl.addWidget(btns)
        dlg.exec()

    def _show_donate(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Donate — Ủng hộ")
        dlg.setMinimumSize(320, 400)
        dl = QVBoxLayout(dlg)
        dl.setSpacing(12)
        dl.setContentsMargins(20, 20, 20, 20)
        dl.addWidget(QLabel("Quét mã QR để donate ủng hộ tác giả:"))
        from PySide6.QtGui import QPixmap
        img_label = QLabel()
        img_path = Path(__file__).parent / "qrdonate.jpg"
        if img_path.exists():
            pix = QPixmap(str(img_path))
            img_label.setPixmap(pix.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            img_label.setText(f"Chưa có file: assets/qrdonate.jpg")
            img_label.setStyleSheet("color: #9ca3af;")
        img_label.setAlignment(Qt.AlignCenter)
        dl.addWidget(img_label)
        dl.addWidget(QLabel("Cảm ơn bạn đã ủng hộ!"))
        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.accepted.connect(dlg.accept)
        dl.addWidget(btns)
        dlg.exec()


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION PAGE (Tab 2) — Full-width session management
# ═══════════════════════════════════════════════════════════════════════════════

class SessionPage(QWidget):
    def __init__(self, max_sessions: int = 3):
        super().__init__()
        self.max_sessions = max_sessions
        self._build()
        self.reload()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(16)
        lay.setContentsMargins(24, 20, 24, 20)

        # Header
        hdr = QHBoxLayout()
        h = QLabel("Quản Lý Session")
        h.setStyleSheet("font-size: 20px; font-weight: 700; color: #1a1a2e;")
        hdr.addWidget(h)
        hdr.addStretch()

        # Stats
        self.stat_lbl = QLabel("")
        self.stat_lbl.setObjectName("mutedLabel")
        hdr.addWidget(self.stat_lbl)
        lay.addLayout(hdr)

        # Buttons
        btns = QHBoxLayout()
        btns.setSpacing(8)

        btn_add = QPushButton("Thêm Session")
        btn_add.setStyleSheet("""
            QPushButton { background-color: #2563eb; color: #ffffff; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; font-size: 12px; min-height: 32px; }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._add)
        btns.addWidget(btn_add)

        btn_refresh = QPushButton("Kiểm tra tất cả")
        btn_refresh.setStyleSheet("""
            QPushButton { background-color: #ffffff; color: #374151; border: 1.5px solid #d1d5db; border-radius: 6px; padding: 7px 14px; font-weight: 500; font-size: 12px; min-height: 32px; }
            QPushButton:hover { background-color: #f3f4f6; border-color: #9ca3af; }
        """)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self._refresh_all)
        btns.addWidget(btn_refresh)

        btn_del = QPushButton("Xoá đã chọn")
        btn_del.setStyleSheet("""
            QPushButton { background-color: #ffffff; color: #dc2626; border: 1.5px solid #fca5a5; border-radius: 6px; padding: 7px 14px; font-weight: 500; font-size: 12px; min-height: 32px; }
            QPushButton:hover { background-color: #fef2f2; }
        """)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.clicked.connect(self._delete)
        btns.addWidget(btn_del)

        btn_rename = QPushButton("Đổi tên")
        btn_rename.setStyleSheet("""
            QPushButton { background-color: #ffffff; color: #374151; border: 1.5px solid #d1d5db; border-radius: 6px; padding: 7px 14px; font-weight: 500; font-size: 12px; min-height: 32px; }
            QPushButton:hover { background-color: #f3f4f6; border-color: #9ca3af; }
        """)
        btn_rename.setCursor(Qt.PointingHandCursor)
        btn_rename.clicked.connect(self._rename)
        btns.addWidget(btn_rename)

        btns.addStretch()
        lay.addLayout(btns)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Tên", "Email", "Loại", "Trạng thái", "Quota", "Thành công", "Thất bại"
        ])
        hdr_t = self.table.horizontalHeader()
        hdr_t.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr_t.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, 7):
            hdr_t.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        lay.addWidget(self.table)

    def reload(self):
        # Tự động xóa sessions bị lỗi
        accounts = account_service.list_accounts()
        error_tokens = [a["access_token"] for a in accounts if a.get("status") in ("异常", "禁用")]
        if error_tokens:
            for t in error_tokens:
                set_account_name(t, "")
            account_service.delete_accounts(error_tokens)
            accounts = account_service.list_accounts()

        self.table.setRowCount(len(accounts))
        STATUS = {"正常": "Hoạt động", "限流": "Giới hạn", "异常": "Lỗi", "禁用": "Tắt"}
        TYPE = {"free": "Miễn phí", "plus": "Plus", "team": "Team", "pro": "Pro"}

        active = sum(1 for a in accounts if a.get("status") == "正常")
        self.stat_lbl.setText(f"{len(accounts)}/{self.max_sessions} sessions · {active} hoạt động")

        for row, acc in enumerate(accounts):
            token = acc.get("access_token", "")
            name = get_account_name(token) or (token[:12] + "...")
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, token)
            self.table.setItem(row, 0, name_item)

            self.table.setItem(row, 1, QTableWidgetItem(acc.get("email") or "—"))
            self.table.setItem(row, 2, QTableWidgetItem(TYPE.get(acc.get("type", ""), acc.get("type", ""))))

            status = acc.get("status", "正常")
            si = QTableWidgetItem(STATUS.get(status, status))
            if status == "正常":
                si.setForeground(QColor("#059669"))
            elif status == "限流":
                si.setForeground(QColor("#d97706"))
            else:
                si.setForeground(QColor("#dc2626"))
            self.table.setItem(row, 3, si)

            q = "?" if acc.get("image_quota_unknown") else str(acc.get("quota", 0))
            self.table.setItem(row, 4, QTableWidgetItem(q))
            self.table.setItem(row, 5, QTableWidgetItem(str(acc.get("success", 0))))
            self.table.setItem(row, 6, QTableWidgetItem(str(acc.get("fail", 0))))

    def _add(self):
        # Kiểm tra giới hạn max_sessions từ D1
        current_count = len(account_service.list_accounts())
        if current_count >= self.max_sessions:
            QMessageBox.warning(
                self, "Đã đạt giới hạn",
                f"Tài khoản của bạn chỉ được thêm tối đa {self.max_sessions} session token.\n"
                f"Hiện tại: {current_count}/{self.max_sessions}\n\n"
                "Liên hệ admin để nâng cấp giới hạn."
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Thêm Session")
        dlg.setMinimumWidth(520)
        dl = QVBoxLayout(dlg)
        dl.setSpacing(12)
        dl.setContentsMargins(20, 20, 20, 20)

        dl.addWidget(QLabel("Tên (tuỳ chọn):"))
        name_input = QLineEdit()
        name_input.setPlaceholderText("VD: Account Plus 1")
        dl.addWidget(name_input)

        dl.addWidget(QLabel("Dán một trong các dạng sau:"))
        hint = QLabel("• Access Token (bắt đầu bằng ey...)\n• JSON response từ /api/auth/session\n• Cookies JSON (export từ browser)")
        hint.setStyleSheet("color: #6b7280; font-size: 11px;")
        dl.addWidget(hint)

        token_input = QTextEdit()
        token_input.setPlaceholderText("Dán access token, JSON response, hoặc cookies JSON vào đây...")
        token_input.setMinimumHeight(180)
        dl.addWidget(token_input)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        dl.addWidget(btns)

        if dlg.exec() != QDialog.Accepted:
            return

        text = token_input.toPlainText().strip()
        if not text:
            return

        name = name_input.text().strip()
        tokens = self._extract_tokens(text)

        if not tokens:
            QMessageBox.warning(self, "Lỗi",
                "Không tìm thấy token hợp lệ.\n\n"
                "Hỗ trợ:\n"
                "• Access token trực tiếp (ey...)\n"
                "• JSON có chứa 'accessToken'\n"
                "• Cookies JSON (sẽ tự lấy token từ ChatGPT)")
            return

        for i, t in enumerate(tokens):
            if name:
                set_account_name(t, name if len(tokens) == 1 else f"{name} #{i+1}")

        result = account_service.add_accounts(tokens)
        for t in tokens:
            acc = account_service.get_account(t)
            if acc and acc.get("quota", 0) == 0 and not acc.get("image_quota_unknown"):
                account_service.update_account(t, {"image_quota_unknown": True})

        self.reload()
        QMessageBox.information(self, "OK", f"Đã thêm {result['added']} session.")

    def _extract_tokens(self, text: str) -> list:
        """Trích xuất access tokens từ nhiều dạng input"""
        tokens = []

        # Thử parse JSON
        try:
            data = json.loads(text)

            # Dạng 1: JSON response có accessToken
            if isinstance(data, dict) and "accessToken" in data:
                return [data["accessToken"]]

            # Dạng 2: Cookies JSON array
            if isinstance(data, list) and len(data) > 0 and "domain" in data[0]:
                token = self._get_token_from_cookies(data)
                if token:
                    return [token]
                return []

        except (json.JSONDecodeError, TypeError):
            pass

        # Dạng 3: Plain token(s)
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("ey") and len(line) > 100:
                tokens.append(line)

        return tokens

    def _get_token_from_cookies(self, cookies: list) -> str:
        """Dùng cookies để gọi /api/auth/session và lấy accessToken"""
        try:
            from curl_cffi import requests as cffi_requests

            # Build cookie string
            cookie_str = "; ".join(
                f"{c['name']}={c['value']}" for c in cookies
                if c.get("domain", "").endswith("chatgpt.com") and c.get("name") and c.get("value")
            )

            if not cookie_str:
                return ""

            # Gọi /api/auth/session
            resp = cffi_requests.get(
                "https://chatgpt.com/api/auth/session",
                headers={
                    "Cookie": cookie_str,
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                },
                impersonate="chrome",
                timeout=30,
            )

            if resp.status_code == 200:
                data = resp.json()
                token = data.get("accessToken", "")
                if token:
                    return token

            return ""
        except Exception as e:
            logger.error(f"Lỗi lấy token từ cookies: {e}")
            return ""

    def _refresh_all(self):
        accounts = account_service.list_accounts()
        if not accounts:
            QMessageBox.warning(self, "Trống", "Chưa có session nào.")
            return
        before_count = len(accounts)
        tokens = [a["access_token"] for a in accounts]
        self._rw = RefreshWorker(tokens)
        self._rw.finished.connect(self._on_refresh_done)
        self._rw.start()

    def _on_refresh_done(self, result):
        refreshed = result.get("refreshed", 0)
        errors = result.get("errors", [])
        # Chỉ reload nếu có cập nhật thành công
        if refreshed > 0:
            self.reload()
        msg = f"Đã kiểm tra xong.\nCập nhật: {refreshed} session."
        if errors:
            msg += f"\n\nKhông kiểm tra được {len(errors)} session:"
            for err in errors[:3]:
                msg += f"\n  • {err.get('token', '?')}: {err.get('error', '')[:40]}"
            msg += "\n\n(Session không bị xoá, chỉ không cập nhật được)"
        QMessageBox.information(self, "Kết quả", msg)

    def _delete(self):
        rows = set(item.row() for item in self.table.selectedItems())
        if not rows:
            return
        reply = QMessageBox.question(self, "Xác nhận", f"Xoá {len(rows)} session?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        tokens = [self.table.item(r, 0).data(Qt.UserRole) for r in rows if self.table.item(r, 0)]
        tokens = [t for t in tokens if t]
        for t in tokens:
            set_account_name(t, "")
        account_service.delete_accounts(tokens)
        self.reload()

    def _rename(self):
        rows = set(item.row() for item in self.table.selectedItems())
        if len(rows) != 1:
            QMessageBox.warning(self, "Chọn 1", "Chọn đúng 1 session để đổi tên.")
            return
        row = list(rows)[0]
        token = self.table.item(row, 0).data(Qt.UserRole)
        if not token:
            return
        current = get_account_name(token) or ""
        new_name, ok = QInputDialog.getText(self, "Đổi tên", "Tên mới:", text=current)
        if ok:
            set_account_name(token, new_name)
            self.reload()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH API URL
# ═══════════════════════════════════════════════════════════════════════════════
AUTH_API_URL = "https://image-gen-admin-2xn.pages.dev/api/auth"


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN / REGISTER DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class LoginDialog(QDialog):
    """Màn hình đăng nhập / đăng ký"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Imagine GPT")
        self.setFixedSize(420, 420)
        self.user_data = None
        self._mode = "login"  # "login" or "register"
        self._build()

    def _build(self):
        # Override stylesheet cho dialog này
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QWidget { background-color: transparent; color: #1a1a2e; font-family: -apple-system, "Segoe UI", sans-serif; font-size: 14px; }
            QLineEdit {
                background-color: #f9fafb;
                border: 1.5px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px 14px;
                font-size: 14px;
                color: #1a1a2e;
            }
            QLineEdit:focus { border: 1.5px solid #2563eb; background-color: #fff; }
            QPushButton#loginBtn {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton#loginBtn:hover { background-color: #1d4ed8; }
            QPushButton#switchBtn {
                background-color: transparent;
                color: #2563eb;
                border: none;
                font-size: 13px;
                padding: 4px;
            }
            QPushButton#switchBtn:hover { color: #1d4ed8; }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Top accent bar
        bar = QWidget()
        bar.setFixedHeight(5)
        bar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2563eb, stop:1 #7c3aed);")
        outer.addWidget(bar)

        # Content
        content = QWidget()
        content.setStyleSheet("background: #ffffff;")
        lay = QVBoxLayout(content)
        lay.setSpacing(16)
        lay.setContentsMargins(40, 36, 40, 36)

        # Logo / Title
        title = QLabel("Imagine GPT")
        title.setStyleSheet("font-size: 26px; font-weight: 700; color: #1a1a2e; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        self.subtitle = QLabel("Đăng nhập để tiếp tục")
        self.subtitle.setStyleSheet("color: #6b7280; font-size: 13px; background: transparent;")
        self.subtitle.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.subtitle)

        lay.addSpacing(8)

        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedHeight(46)
        lay.addWidget(self.username_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(46)
        self.password_input.returnPressed.connect(self._submit)
        lay.addWidget(self.password_input)

        # Error/success message
        self.msg_label = QLabel("")
        self.msg_label.setStyleSheet("color: #dc2626; font-size: 12px; background: transparent;")
        self.msg_label.setWordWrap(True)
        self.msg_label.setAlignment(Qt.AlignCenter)
        self.msg_label.setFixedHeight(32)
        lay.addWidget(self.msg_label)

        # Submit button
        self.submit_btn = QPushButton("Đăng nhập")
        self.submit_btn.setFixedHeight(46)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:pressed { background-color: #1e40af; }
            QPushButton:disabled { background-color: #93c5fd; color: #ffffff; }
        """)
        self.submit_btn.clicked.connect(self._submit)
        lay.addWidget(self.submit_btn)

        # Switch mode
        switch_row = QHBoxLayout()
        switch_row.setAlignment(Qt.AlignCenter)
        self.switch_hint = QLabel("Chưa có tài khoản?")
        self.switch_hint.setStyleSheet("color: #6b7280; font-size: 13px; background: transparent;")
        self.switch_btn = QPushButton("Đăng ký ngay")
        self.switch_btn.setObjectName("switchBtn")
        self.switch_btn.setCursor(Qt.PointingHandCursor)
        self.switch_btn.clicked.connect(self._toggle_mode)
        switch_row.addWidget(self.switch_hint)
        switch_row.addWidget(self.switch_btn)
        lay.addLayout(switch_row)

        outer.addWidget(content)

    def _toggle_mode(self):
        if self._mode == "login":
            self._mode = "register"
            self.subtitle.setText("Tạo tài khoản mới")
            self.submit_btn.setText("Đăng ký")
            self.switch_hint.setText("Đã có tài khoản?")
            self.switch_btn.setText("Đăng nhập")
        else:
            self._mode = "login"
            self.subtitle.setText("Đăng nhập để tiếp tục")
            self.submit_btn.setText("Đăng nhập")
            self.switch_hint.setText("Chưa có tài khoản?")
            self.switch_btn.setText("Đăng ký ngay")
        self.msg_label.setText("")
        self.username_input.clear()
        self.password_input.clear()

    def _submit(self):
        self.msg_label.setStyleSheet("color: #dc2626; font-size: 12px; background: transparent;")
        self.msg_label.setText("")
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            self.msg_label.setText("Vui lòng nhập username và password.")
            return

        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Đang xử lý...")

        try:
            from curl_cffi import requests as cffi_requests
            resp = cffi_requests.post(
                AUTH_API_URL,
                json={"action": self._mode, "username": username, "password": password},
                timeout=15,
                impersonate="chrome"
            )
            # Handle non-JSON response
            content_type = resp.headers.get("content-type", "")
            if "json" not in content_type:
                self.msg_label.setText(f"Lỗi server (HTTP {resp.status_code}). Thử lại sau.")
                self.submit_btn.setEnabled(True)
                self.submit_btn.setText("Đăng nhập" if self._mode == "login" else "Đăng ký")
                return
            data = resp.json()
        except Exception as e:
            err = str(e)
            if "unexpected character" in err or "json" in err.lower():
                self.msg_label.setText("Lỗi server. Vui lòng thử lại sau.")
            else:
                self.msg_label.setText(f"Lỗi kết nối: {err[:60]}")
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Đăng nhập" if self._mode == "login" else "Đăng ký")
            return

        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("Đăng nhập" if self._mode == "login" else "Đăng ký")

        if data.get("ok"):
            if self._mode == "login":
                self.user_data = data.get("user")
                self.accept()
            else:
                self.msg_label.setStyleSheet("color: #059669; font-size: 12px; background: transparent;")
                self.msg_label.setText(data.get("message", "Đăng ký thành công! Hãy đăng nhập."))
                self._toggle_mode()
        else:
            self.msg_label.setText(data.get("error", "Thất bại"))


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setApplicationName("Image Generator")

    # Login required
    login = LoginDialog()
    if login.exec() != QDialog.Accepted:
        sys.exit(0)

    # User authenticated — lưu max_sessions từ D1
    user_data = login.user_data
    max_sessions = user_data.get("max_sessions", 3)

    win = MainWindow(max_sessions=max_sessions)
    win.setWindowTitle(f"Image Generator v1.0 — {user_data.get('username', '')}")
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
