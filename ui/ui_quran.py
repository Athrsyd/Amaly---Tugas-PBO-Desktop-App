"""
Al-Qur'an Page - AMALY
Surat list → detail ayat, bookmark, target baca, sukai ayat.
Data from equran.id API v2.
"""

import os
import threading
import requests

from PyQt6.QtCore import Qt, pyqtSignal, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QColor, QPixmap, QFont
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QLineEdit, QProgressBar, QScrollArea, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget, QPushButton, QComboBox, QStackedWidget,
)

from ui.ui_dashboard import IconWidget

UI_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.abspath(os.path.join(UI_DIR, ".."))
ASSET_DIR = os.path.join(APP_DIR, "images")
API_BASE = "https://equran.id/api/v2"


# ═══════════════════════════════════════════════════════════════
#  HELPER: cumulative ayat index for progress calculation
# ═══════════════════════════════════════════════════════════════
_surat_ayat_cache = []  # [(nomor, jumlahAyat, namaLatin), ...]


def _cum_ayat_index(surat_list, surat_no, ayat_no):
    """Return a global ayat index (1-based) given surat number and ayat number."""
    total = 0
    for s in surat_list:
        if s["nomor"] < surat_no:
            total += s["jumlahAyat"]
        elif s["nomor"] == surat_no:
            total += ayat_no
            break
    return total


# ═══════════════════════════════════════════════════════════════
#  QURAN PAGE
# ═══════════════════════════════════════════════════════════════
class QuranPage(QWidget):
    back_to_dashboard = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = None
        self._surat_list = []
        self._current_surat = None  # dict with ayat
        self._search_text = ""
        self._arab_font_size = 24
        self.setup_ui()
        self._load_surat_list()

    def set_user_data(self, data):
        if not data:
            return
        self.user_id = data.get("id")
        saved = self.db.get_setting(self.user_id, "arab_font_size", "24")
        self._arab_font_size = int(saved)
        self._refresh_bookmark_display()
        self._refresh_target_display()

    def set_arab_font_size(self, size):
        self._arab_font_size = size

    # ─────────────── ROOT LAYOUT ───────────────
    def setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.list_page = self._build_list_page()
        self.detail_page = self._build_detail_page()
        self.stack.addWidget(self.list_page)
        self.stack.addWidget(self.detail_page)
        root.addWidget(self.stack, 1)

    # ─────────────── SIDEBAR ───────────────
    def _build_sidebar(self):
        sb = QFrame()
        sb.setFixedWidth(220)
        sb.setObjectName("sidebar")
        sb.setStyleSheet("""
            QFrame#sidebar {
                background-color: #1A3C2A;
                border-top-right-radius: 28px;
                border-bottom-right-radius: 28px;
            }
        """)
        lay = QVBoxLayout(sb)
        lay.setContentsMargins(20, 28, 20, 28)
        lay.setSpacing(0)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(10)
        logo_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        logo_pixmap = QPixmap(os.path.join(ASSET_DIR, "logo.png"))
        logo_img = QLabel()
        if logo_pixmap and not logo_pixmap.isNull():
            logo_img.setPixmap(logo_pixmap.scaled(44, 44,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        logo_img.setStyleSheet("background:transparent;")
        logo_row.addWidget(logo_img)
        logo_text = QLabel("AMALY")
        logo_text.setStyleSheet(
            "color:#FFF;font-size:20px;font-weight:bold;background:transparent;letter-spacing:4px;")
        logo_row.addWidget(logo_text)
        lay.addLayout(logo_row)
        lay.addSpacing(42)

        menu = [
            ("home", "Dashboard", False),
            ("mosque", "Jadwal Sholat", False),
            ("book", "Al-Qur'an", True),
            ("chart", "Sedekah Tracker", False),
        ]
        self._sb_btns = {}
        for ic, label, active in menu:
            btn = self._sidebar_btn(ic, label, active)
            self._sb_btns[label] = btn
            lay.addWidget(btn)
            lay.addSpacing(4)

        self._sb_btns["Dashboard"].mousePressEvent = lambda e: self.back_to_dashboard.emit()

        lay.addStretch()
        lay.addWidget(self._sidebar_btn("gear", "Settings", False))
        return sb

    def _sidebar_btn(self, icon_name, text, active):
        btn = QWidget()
        btn.setFixedHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        h = QHBoxLayout(btn)
        h.setContentsMargins(16, 0, 12, 0)
        h.setSpacing(12)
        ic_color = QColor("#FFF") if active else QColor(255, 255, 255, 140)
        h.addWidget(IconWidget(icon_name, 20, ic_color))
        lbl = QLabel(text)
        fw = "bold" if active else "normal"
        c = "#FFF" if active else "rgba(255,255,255,140)"
        lbl.setStyleSheet(f"color:{c};font-size:14px;font-weight:{fw};background:transparent;")
        h.addWidget(lbl)
        h.addStretch()
        bg = "rgba(255,255,255,15)" if active else "transparent"
        btn.setStyleSheet(f"background:{bg};border-radius:12px;")
        return btn

    # ═══════════════════════════════════════════
    #  PAGE 1: SURAT LIST
    # ═══════════════════════════════════════════
    def _build_list_page(self):
        page = QWidget()
        page.setStyleSheet("background-color:#ECEEE7;")
        col = QVBoxLayout(page)
        col.setContentsMargins(28, 20, 28, 12)
        col.setSpacing(0)

        # Header
        header = QHBoxLayout()
        title = QLabel("Al-Qur'an")
        title.setStyleSheet("font-size:24px;font-weight:bold;color:#1A3C2A;background:transparent;")
        header.addWidget(title)
        header.addStretch()
        col.addLayout(header)
        col.addSpacing(12)

        # Bookmark + Target cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        cards_row.addWidget(self._build_bookmark_card())
        cards_row.addWidget(self._build_target_card())
        col.addLayout(cards_row)
        col.addSpacing(14)

        # Search
        search_row = QHBoxLayout()
        search_wrap = QWidget()
        search_wrap.setFixedHeight(40)
        search_wrap.setStyleSheet("background-color:#E2E4DD;border-radius:20px;")
        sw_h = QHBoxLayout(search_wrap)
        sw_h.setContentsMargins(16, 0, 16, 0)
        sw_h.setSpacing(8)
        sw_h.addWidget(IconWidget("search", 16, QColor("#999")))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari surat...")
        self.search_input.setStyleSheet(
            "QLineEdit{background:transparent;border:none;font-size:13px;color:#555;}"
            "QLineEdit::placeholder{color:#999;}")
        self.search_input.textChanged.connect(self._on_search)
        sw_h.addWidget(self.search_input)
        search_row.addWidget(search_wrap, 1)
        col.addLayout(search_row)
        col.addSpacing(10)

        # Surat list scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollBar:vertical{background:#E4E8DE;width:6px;border-radius:3px;}"
            "QScrollBar::handle:vertical{background:#B0C4A8;border-radius:3px;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.surat_list_widget = QWidget()
        self.surat_list_widget.setStyleSheet("background:transparent;")
        self.surat_list_layout = QVBoxLayout(self.surat_list_widget)
        self.surat_list_layout.setContentsMargins(0, 0, 4, 0)
        self.surat_list_layout.setSpacing(6)
        self.surat_list_layout.addStretch()

        scroll.setWidget(self.surat_list_widget)
        col.addWidget(scroll)
        return page

    # ── Bookmark Mini Card ──
    def _build_bookmark_card(self):
        card = QFrame()
        card.setObjectName("bmCard")
        card.setStyleSheet("""
            QFrame#bmCard {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #1A3C2A, stop:1 #2D6B4A);
                border-radius: 16px;
            }
        """)
        card.setFixedHeight(100)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16); shadow.setColor(QColor(0,0,0,25)); shadow.setOffset(0,4)
        card.setGraphicsEffect(shadow)

        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(4)
        t = QLabel("Terakhir Dibaca")
        t.setStyleSheet("color:rgba(255,255,255,170);font-size:11px;background:transparent;")
        v.addWidget(t)
        self.bm_label = QLabel("Belum ada bookmark")
        self.bm_label.setStyleSheet("color:#FFF;font-size:15px;font-weight:bold;background:transparent;")
        self.bm_label.setWordWrap(True)
        v.addWidget(self.bm_label)
        v.addStretch()
        lnk = QLabel("Lanjutkan →")
        lnk.setStyleSheet("color:rgba(255,255,255,150);font-size:11px;background:transparent;")
        v.addWidget(lnk)

        card.mousePressEvent = lambda e: self._open_bookmark()
        return card

    # ── Target Card ──
    def _build_target_card(self):
        card = QFrame()
        card.setObjectName("tgtCard")
        card.setStyleSheet("""
            QFrame#tgtCard {
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid rgba(0,0,0,6);
            }
        """)
        card.setFixedHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16); shadow.setColor(QColor(0,0,0,15)); shadow.setOffset(0,4)
        card.setGraphicsEffect(shadow)

        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(4)
        t = QLabel("Target Baca")
        t.setStyleSheet("color:#999;font-size:11px;background:transparent;")
        v.addWidget(t)
        self.target_info_label = QLabel("Belum diatur")
        self.target_info_label.setStyleSheet("color:#1A3C2A;font-size:13px;font-weight:bold;background:transparent;")
        self.target_info_label.setWordWrap(True)
        v.addWidget(self.target_info_label)
        self.target_bar = QProgressBar()
        self.target_bar.setValue(0)
        self.target_bar.setTextVisible(False)
        self.target_bar.setFixedHeight(8)
        self.target_bar.setStyleSheet("""
            QProgressBar{background:#E4E8DE;border:none;border-radius:4px;}
            QProgressBar::chunk{background:#2D6B4A;border-radius:4px;}""")
        v.addWidget(self.target_bar)
        self.target_pct_label = QLabel("")
        self.target_pct_label.setStyleSheet("color:#2D6B4A;font-size:11px;background:transparent;")
        v.addWidget(self.target_pct_label)
        return card

    # ═══════════════════════════════════════════
    #  PAGE 2: SURAT DETAIL
    # ═══════════════════════════════════════════
    def _build_detail_page(self):
        page = QWidget()
        page.setStyleSheet("background-color:#ECEEE7;")
        col = QVBoxLayout(page)
        col.setContentsMargins(28, 20, 28, 12)
        col.setSpacing(0)

        # Back + surat title
        top = QHBoxLayout()
        back_btn = QPushButton("← Kembali")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background:transparent; color:#2D6B4A; font-size:13px;
                font-weight:bold; border:none; padding:4px 0;
            }
            QPushButton:hover { color:#1A3C2A; }
        """)
        back_btn.clicked.connect(self._back_to_list)
        top.addWidget(back_btn)
        top.addStretch()
        self.detail_title = QLabel("")
        self.detail_title.setStyleSheet("font-size:20px;font-weight:bold;color:#1A3C2A;background:transparent;")
        top.addWidget(self.detail_title)
        top.addSpacing(12)
        self.detail_subtitle = QLabel("")
        self.detail_subtitle.setStyleSheet("font-size:13px;color:#777;background:transparent;")
        top.addWidget(self.detail_subtitle)
        top.addStretch()

        # Bookmark button
        self.bm_btn = QPushButton("Tandai Baca Terakhir")
        self.bm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bm_btn.setStyleSheet("""
            QPushButton {
                background:#2D6B4A; color:#FFF; font-size:11px;
                font-weight:bold; border:none; border-radius:14px;
                padding:6px 16px;
            }
            QPushButton:hover { background:#1A3C2A; }
        """)
        self.bm_btn.setVisible(False)
        top.addWidget(self.bm_btn)

        col.addLayout(top)
        col.addSpacing(6)

        # Target set row
        self.target_set_frame = QFrame()
        self.target_set_frame.setStyleSheet("""
            QFrame { background:#FFF; border-radius:12px; border:1px solid rgba(0,0,0,6); }
        """)
        self.target_set_frame.setFixedHeight(48)
        tgt_h = QHBoxLayout(self.target_set_frame)
        tgt_h.setContentsMargins(14, 0, 14, 0)
        tgt_h.setSpacing(8)
        tgt_lbl = QLabel("Set Target:")
        tgt_lbl.setStyleSheet("font-size:12px;color:#555;background:transparent;font-weight:bold;")
        tgt_h.addWidget(tgt_lbl)
        tgt_h.addWidget(QLabel("Ayat"))
        self.target_start_spin = QSpinBox()
        self.target_start_spin.setMinimum(1)
        self.target_start_spin.setStyleSheet("QSpinBox{border:1px solid #CCC;border-radius:4px;padding:2px 6px;color:#000;} QSpinBox QAbstractSpinBox { color: #000; }")
        tgt_h.addWidget(self.target_start_spin)
        tgt_h.addWidget(QLabel("s/d"))
        self.target_end_spin = QSpinBox()
        self.target_end_spin.setMinimum(1)
        self.target_end_spin.setStyleSheet("QSpinBox{border:1px solid #CCC;border-radius:4px;padding:2px 6px;color:#000;} QSpinBox QAbstractSpinBox { color: #000; }")
        tgt_h.addWidget(self.target_end_spin)
        tgt_save = QPushButton("Simpan Target")
        tgt_save.setCursor(Qt.CursorShape.PointingHandCursor)
        tgt_save.setStyleSheet("""
            QPushButton{background:#2D6B4A;color:#FFF;font-size:11px;font-weight:bold;
            border:none;border-radius:10px;padding:5px 14px;}
            QPushButton:hover{background:#1A3C2A;}""")
        tgt_save.clicked.connect(self._save_target)
        tgt_h.addWidget(tgt_save)
        tgt_h.addStretch()
        col.addWidget(self.target_set_frame)
        col.addSpacing(8)

        # Surat info banner
        self.surat_info_banner = QFrame()
        self.surat_info_banner.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #1A3C2A, stop:1 #2D6B4A);
                border-radius: 16px;
            }
        """)
        self.surat_info_banner.setFixedHeight(90)
        ban_v = QVBoxLayout(self.surat_info_banner)
        ban_v.setContentsMargins(24, 14, 24, 14)
        ban_v.setSpacing(2)
        self.surat_arab_label = QLabel("")
        self.surat_arab_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.surat_arab_label.setStyleSheet("font-size:28px;color:#FFD88E;background:transparent;")
        self.surat_arab_label.setFont(QFont("Traditional Arabic", 28))
        ban_v.addWidget(self.surat_arab_label)
        self.surat_meta_label = QLabel("")
        self.surat_meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.surat_meta_label.setStyleSheet("font-size:12px;color:rgba(255,255,255,160);background:transparent;")
        ban_v.addWidget(self.surat_meta_label)
        col.addWidget(self.surat_info_banner)
        col.addSpacing(8)

        # Ayat scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollBar:vertical{background:#E4E8DE;width:6px;border-radius:3px;}"
            "QScrollBar::handle:vertical{background:#B0C4A8;border-radius:3px;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.ayat_list_widget = QWidget()
        self.ayat_list_widget.setStyleSheet("background:transparent;")
        self.ayat_list_layout = QVBoxLayout(self.ayat_list_widget)
        self.ayat_list_layout.setContentsMargins(0, 0, 4, 0)
        self.ayat_list_layout.setSpacing(0)
        self.ayat_list_layout.addStretch()
        scroll.setWidget(self.ayat_list_widget)
        col.addWidget(scroll)

        # Loading label
        self.detail_loading = QLabel("Memuat ayat...")
        self.detail_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_loading.setStyleSheet("font-size:14px;color:#999;background:transparent;padding:40px;")
        self.ayat_list_layout.insertWidget(0, self.detail_loading)

        return page

    # ═══════════════════════════════════════════
    #  API: LOAD SURAT LIST
    # ═══════════════════════════════════════════
    def _load_surat_list(self):
        def fetch():
            try:
                r = requests.get(f"{API_BASE}/surat", timeout=15)
                data = r.json().get("data", [])
                QMetaObject.invokeMethod(
                    self, "_set_surat_list",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(list, data))
            except Exception:
                QMetaObject.invokeMethod(
                    self, "_set_surat_list",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(list, []))
        threading.Thread(target=fetch, daemon=True).start()

    @pyqtSlot(list)
    def _set_surat_list(self, data):
        global _surat_ayat_cache
        self._surat_list = data
        _surat_ayat_cache = [{"nomor": s["nomor"], "jumlahAyat": s["jumlahAyat"],
                              "namaLatin": s["namaLatin"]} for s in data]
        self._render_surat_list()

    def _render_surat_list(self):
        # Clear
        while self.surat_list_layout.count():
            item = self.surat_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        search = self._search_text.lower()
        for s in self._surat_list:
            if search and search not in s["namaLatin"].lower() and search not in s.get("arti", "").lower() and search not in str(s["nomor"]):
                continue
            self.surat_list_layout.addWidget(self._surat_row(s))
        self.surat_list_layout.addStretch()

    def _surat_row(self, surat):
        row = QFrame()
        row.setFixedHeight(64)
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 14px;
                border: 1px solid rgba(0,0,0,5);
            }
            QFrame:hover { background: #F5F8F2; }
        """)
        h = QHBoxLayout(row)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(14)

        # Number badge
        badge = QLabel(str(surat["nomor"]))
        badge.setFixedSize(34, 34)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("""
            QLabel {
                background: #EAF5E6; color: #2D6B4A;
                font-size: 12px; font-weight: bold;
                border-radius: 17px;
            }
        """)
        h.addWidget(badge)

        # Name
        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        latin = QLabel(surat["namaLatin"])
        latin.setStyleSheet("font-size:14px;font-weight:bold;color:#333;background:transparent;")
        name_col.addWidget(latin)
        meta = QLabel(f"{surat.get('arti', '')} · {surat['jumlahAyat']} ayat · {surat.get('tempatTurun', '')}")
        meta.setStyleSheet("font-size:11px;color:#999;background:transparent;")
        name_col.addWidget(meta)
        h.addLayout(name_col, 1)

        # Arabic name
        arab = QLabel(surat["nama"])
        arab.setStyleSheet("font-size:20px;color:#2D6B4A;background:transparent;")
        arab.setFont(QFont("Traditional Arabic", 20))
        h.addWidget(arab)

        row.mousePressEvent = lambda e, s=surat: self._open_surat(s["nomor"])
        return row

    def _on_search(self, text):
        self._search_text = text
        self._render_surat_list()

    # ═══════════════════════════════════════════
    #  OPEN SURAT DETAIL
    # ═══════════════════════════════════════════
    def _open_surat(self, nomor):
        self.stack.setCurrentWidget(self.detail_page)
        self.detail_loading.setVisible(True)
        self.detail_loading.setText("Memuat ayat...")
        self.bm_btn.setVisible(False)

        # Find surat info from cache
        surat_info = None
        for s in self._surat_list:
            if s["nomor"] == nomor:
                surat_info = s
                break
        if surat_info:
            self.detail_title.setText(surat_info["namaLatin"])
            self.detail_subtitle.setText(f"{surat_info.get('arti', '')} · {surat_info['jumlahAyat']} ayat")
            self.surat_arab_label.setText(surat_info["nama"])
            self.surat_meta_label.setText(
                f"{surat_info['tempatTurun']} · {surat_info['jumlahAyat']} Ayat")
            self.target_start_spin.setMaximum(surat_info["jumlahAyat"])
            self.target_end_spin.setMaximum(surat_info["jumlahAyat"])
            self.target_end_spin.setValue(surat_info["jumlahAyat"])

        def fetch():
            try:
                r = requests.get(f"{API_BASE}/surat/{nomor}", timeout=15)
                data = r.json().get("data", {})
                QMetaObject.invokeMethod(
                    self, "_set_surat_detail",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(dict, data))
            except Exception:
                QMetaObject.invokeMethod(
                    self, "_set_surat_detail",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(dict, {}))
        threading.Thread(target=fetch, daemon=True).start()

    @pyqtSlot(dict)
    def _set_surat_detail(self, data):
        self._current_surat = data
        self.detail_loading.setVisible(False)

        # Clear existing ayat widgets (keep detail_loading alive)
        while self.ayat_list_layout.count():
            item = self.ayat_list_layout.takeAt(0)
            w = item.widget()
            if w and w is not self.detail_loading:
                w.deleteLater()

        if not data or "ayat" not in data:
            lbl = QLabel("Gagal memuat data surat.")
            lbl.setStyleSheet("font-size:14px;color:#999;background:transparent;padding:40px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ayat_list_layout.addWidget(lbl)
            self.ayat_list_layout.addStretch()
            return

        surat_nomor = data.get("nomor", 0)
        surat_nama = data.get("namaLatin", "")
        self.bm_btn.setVisible(True)
        try:
            self.bm_btn.disconnect()  # clear old connections
        except TypeError:
            pass

        for ayat in data["ayat"]:
            self.ayat_list_layout.addWidget(
                self._ayat_widget(surat_nomor, surat_nama, ayat))

        self.ayat_list_layout.addStretch()

        # Connect bookmark button to bookmark last ayat read (first ayat as default)
        self.bm_btn.clicked.connect(lambda: self._bookmark_dialog(surat_nomor, surat_nama, data["ayat"]))

    def _ayat_widget(self, surat_nomor, surat_nama, ayat):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 14px;
                border: 1px solid rgba(0,0,0,4);
                margin-bottom: 6px;
            }
        """)
        v = QVBoxLayout(frame)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(8)

        # Top: ayat number + actions
        top_h = QHBoxLayout()
        badge = QLabel(str(ayat["nomorAyat"]))
        badge.setFixedSize(30, 30)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("""
            QLabel {
                background: #EAF5E6; color: #2D6B4A;
                font-size: 11px; font-weight: bold;
                border-radius: 15px;
            }
        """)
        top_h.addWidget(badge)
        top_h.addStretch()

        # Bookmark this ayat
        bm_a = QPushButton("📖")
        bm_a.setToolTip("Tandai baca terakhir di ayat ini")
        bm_a.setFixedSize(30, 30)
        bm_a.setCursor(Qt.CursorShape.PointingHandCursor)
        bm_a.setStyleSheet("QPushButton{background:transparent;border:none;font-size:16px;}"
                           "QPushButton:hover{background:#EAF5E6;border-radius:15px;}")
        bm_a.clicked.connect(lambda _, sn=surat_nomor, snm=surat_nama, an=ayat["nomorAyat"]:
                             self._set_bookmark(sn, snm, an))
        top_h.addWidget(bm_a)

        # Like button
        liked = self.db.is_ayat_liked(self.user_id, surat_nomor, ayat["nomorAyat"]) if self.user_id else False
        like_btn = QPushButton("♥" if liked else "♡")
        like_btn.setFixedSize(30, 30)
        like_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        like_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;font-size:18px;"
            f"color:{'#E74C3C' if liked else '#CCC'};}}"
            f"QPushButton:hover{{background:#FEE;border-radius:15px;}}")
        like_btn.clicked.connect(lambda _, btn=like_btn, sn=surat_nomor, snm=surat_nama,
                                 a=ayat: self._toggle_like(btn, sn, snm, a))
        top_h.addWidget(like_btn)
        v.addLayout(top_h)

        # Arabic text
        sz = self._arab_font_size
        arab = QLabel(ayat.get("teksArab", ""))
        arab.setWordWrap(True)
        arab.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        arab.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        arab.setStyleSheet(f"font-size:{sz}px;color:#1A3C2A;background:transparent;line-height:180%;")
        arab.setFont(QFont("Traditional Arabic", sz))
        arab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        arab.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        v.addWidget(arab, 0, Qt.AlignmentFlag.AlignRight)

        # Latin transliteration
        latin = QLabel(ayat.get("teksLatin", ""))
        latin.setWordWrap(True)
        latin.setStyleSheet("font-size:12px;color:#888;background:transparent;font-style:italic;")
        latin.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(latin)

        # Indonesian translation
        indo = QLabel(ayat.get("teksIndonesia", ""))
        indo.setWordWrap(True)
        indo.setStyleSheet("font-size:13px;color:#444;background:transparent;line-height:150%;")
        indo.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(indo)

        return frame

    def _back_to_list(self):
        self.stack.setCurrentWidget(self.list_page)
        self._refresh_bookmark_display()
        self._refresh_target_display()

    # ═══════════════════════════════════════════
    #  BOOKMARK
    # ═══════════════════════════════════════════
    def _set_bookmark(self, surat_nomor, surat_nama, ayat_nomor):
        if not self.user_id:
            return
        self.db.set_bookmark(self.user_id, surat_nomor, surat_nama, ayat_nomor)
        self._refresh_bookmark_display()
        self._refresh_target_display()

    def _bookmark_dialog(self, surat_nomor, surat_nama, ayat_list):
        """Bookmark the last ayat (or user can click individual ayat bookmark button)."""
        if ayat_list:
            self._set_bookmark(surat_nomor, surat_nama, ayat_list[-1]["nomorAyat"])

    def _refresh_bookmark_display(self):
        if not self.user_id:
            return
        bm = self.db.get_bookmark(self.user_id)
        if bm:
            self.bm_label.setText(f"Q.S {bm['surat_nama']} : {bm['ayat_nomor']}")
        else:
            self.bm_label.setText("Belum ada bookmark")

    def _open_bookmark(self):
        if not self.user_id:
            return
        bm = self.db.get_bookmark(self.user_id)
        if bm:
            self._open_surat(bm["surat_nomor"])

    # ═══════════════════════════════════════════
    #  TARGET
    # ═══════════════════════════════════════════
    def _save_target(self):
        if not self.user_id or not self._current_surat:
            return
        surat_nomor = self._current_surat["nomor"]
        surat_nama = self._current_surat["namaLatin"]
        start_ayat = self.target_start_spin.value()
        end_ayat = self.target_end_spin.value()
        if end_ayat < start_ayat:
            end_ayat = start_ayat

        self.db.set_target(
            self.user_id,
            surat_nomor, start_ayat,
            surat_nomor, end_ayat,
            surat_nama, surat_nama
        )
        self._refresh_target_display()

    def _refresh_target_display(self):
        if not self.user_id:
            return
        target = self.db.get_target(self.user_id)
        if not target:
            self.target_info_label.setText("Belum diatur")
            self.target_bar.setValue(0)
            self.target_pct_label.setText("")
            return

        bm = self.db.get_bookmark(self.user_id)
        s_surat = target["start_surat"]
        s_ayat = target["start_ayat"]
        e_surat = target["end_surat"]
        e_ayat = target["end_ayat"]
        s_nama = target["start_surat_nama"]
        e_nama = target["end_surat_nama"]

        # Calculate total ayat in target range
        if self._surat_list:
            start_idx = _cum_ayat_index(self._surat_list, s_surat, s_ayat)
            end_idx = _cum_ayat_index(self._surat_list, e_surat, e_ayat)
            total_target = max(1, end_idx - start_idx + 1)

            # Calculate read progress from bookmark
            read_ayat = 0
            if bm:
                bm_idx = _cum_ayat_index(self._surat_list, bm["surat_nomor"], bm["ayat_nomor"])
                if bm_idx >= start_idx:
                    read_ayat = min(bm_idx - start_idx + 1, total_target)

            pct = int(read_ayat / total_target * 100)
        else:
            total_target = 1
            read_ayat = 0
            pct = 0

        self.target_info_label.setText(
            f"Q.S {s_nama} {s_ayat} → Q.S {e_nama} {e_ayat}")
        self.target_bar.setValue(pct)
        self.target_pct_label.setText(f"{pct}% ({read_ayat}/{total_target} ayat)")

    # ═══════════════════════════════════════════
    #  LIKE AYAT
    # ═══════════════════════════════════════════
    def _toggle_like(self, btn, surat_nomor, surat_nama, ayat):
        if not self.user_id:
            return
        liked = self.db.toggle_liked_ayat(
            self.user_id, surat_nomor, surat_nama,
            ayat["nomorAyat"],
            ayat.get("teksArab", ""),
            ayat.get("teksIndonesia", "")
        )
        if liked:
            btn.setText("♥")
            btn.setStyleSheet(
                "QPushButton{background:transparent;border:none;font-size:18px;color:#E74C3C;}"
                "QPushButton:hover{background:#FEE;border-radius:15px;}")
        else:
            btn.setText("♡")
            btn.setStyleSheet(
                "QPushButton{background:transparent;border:none;font-size:18px;color:#CCC;}"
                "QPushButton:hover{background:#FEE;border-radius:15px;}")
