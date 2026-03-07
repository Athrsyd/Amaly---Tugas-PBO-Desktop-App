"""
Sedekah Tracker Page - AMALY
Input sedekah, progress target bulanan, kalender Hijriyah.
"""

import os
import math
from datetime import date, datetime, timedelta

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap, QFont, QIntValidator, QDoubleValidator
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QFrame, QGraphicsDropShadowEffect, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSpinBox, QVBoxLayout, QWidget,
)

from ui_dashboard import IconWidget

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

KATEGORI_SEDEKAH = [
    "Infaq",
    "Sedekah Jariyah",
    "Zakat",
    "Wakaf",
    "Donasi",
    "Lainnya",
]


# ═══════════════════════════════════════════════════════════════
#  HIJRI CALENDAR CONVERSION (Kuwaiti Algorithm approximation)
# ═══════════════════════════════════════════════════════════════
def gregorian_to_hijri(g_year, g_month, g_day):
    """Convert Gregorian date to approximate Hijri date.
    Returns (h_year, h_month, h_day)."""
    if g_month < 3:
        g_year -= 1
        g_month += 12
    a = math.floor(g_year / 100)
    b = 2 - a + math.floor(a / 4)
    jd = (math.floor(365.25 * (g_year + 4716))
          + math.floor(30.6001 * (g_month + 1))
          + g_day + b - 1524.5)
    # Islamic calendar epoch
    l = math.floor(jd - 1948439.5 + 10632)
    n = math.floor((l - 1) / 10631)
    l = l - 10631 * n + 354
    j = (math.floor((10985 - l) / 5316)
         * math.floor((50 * l) / 17719)
         + math.floor(l / 5670)
         * math.floor((43 * l) / 15238))
    l = (l - math.floor((30 - j) / 15)
         * math.floor((17719 * j) / 50)
         - math.floor(j / 16)
         * math.floor((15238 * j) / 43) + 29)
    h_month = math.floor((24 * l) / 709)
    h_day = l - math.floor((709 * h_month) / 24)
    h_year = 30 * n + j - 30
    return h_year, h_month, h_day


HIJRI_MONTH_NAMES = [
    "", "Muharram", "Safar", "Rabi'ul Awal", "Rabi'ul Akhir",
    "Jumadil Awal", "Jumadil Akhir", "Rajab", "Sya'ban",
    "Ramadhan", "Syawal", "Dzulqa'dah", "Dzulhijjah",
]

HARI_NAMES = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]


def _format_rupiah(val):
    """Format a number to Indonesian rupiah string."""
    if val >= 1_000_000:
        return f"Rp {val / 1_000_000:,.1f} jt"
    if val >= 1_000:
        return f"Rp {val / 1_000:,.0f} rb"
    return f"Rp {val:,.0f}"


# ═══════════════════════════════════════════════════════════════
#  SEDEKAH TRACKER PAGE
# ═══════════════════════════════════════════════════════════════
class SedekahTrackerPage(QWidget):
    back_to_dashboard = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = None
        self._view_month = date.today().month
        self._view_year = date.today().year
        self.setup_ui()

    def set_user_data(self, data):
        if not data:
            return
        self.user_id = data.get("id")
        self._refresh_all()

    # ─────────────── ROOT LAYOUT ───────────────
    def setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), 1)

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
        logo_pixmap = QPixmap(os.path.join(BASE_DIR, "logo.png"))
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
            ("book", "Al-Qur'an", False),
            ("chart", "Sedekah Tracker", True),
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

    # ─────────────── MAIN CONTENT ───────────────
    def _build_content(self):
        wrapper = QWidget()
        wrapper.setStyleSheet("background-color:#ECEEE7;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea{background:#ECEEE7;border:none;}"
            "QScrollBar:vertical{background:#E4E8DE;width:6px;border-radius:3px;}"
            "QScrollBar::handle:vertical{background:#B0C4A8;border-radius:3px;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet("background:transparent;")
        col = QVBoxLayout(content)
        col.setContentsMargins(28, 20, 28, 20)
        col.setSpacing(16)

        # Title
        title = QLabel("Sedekah Tracker")
        title.setStyleSheet("font-size:24px;font-weight:bold;color:#1A3C2A;background:transparent;")
        col.addWidget(title)

        # ── Section 1: Input Form + Target ──
        col.addWidget(self._build_input_section())

        # ── Section 2: Progress Bar ──
        col.addWidget(self._build_progress_section())

        # ── Section 3: Hijri Calendar ──
        col.addWidget(self._build_calendar_section())

        # ── Section 4: Riwayat ──
        col.addWidget(self._build_history_section())

        col.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return wrapper

    # ═══════════════════════════════════════════
    #  SECTION 1: INPUT SEDEKAH + TARGET
    # ═══════════════════════════════════════════
    def _build_input_section(self):
        card = QFrame()
        card.setObjectName("inputCard")
        card.setStyleSheet("""
            QFrame#inputCard {
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid rgba(0,0,0,6);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16); shadow.setColor(QColor(0, 0, 0, 15)); shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(14)

        sec_title = QLabel("Catat Sedekah")
        sec_title.setStyleSheet("font-size:16px;font-weight:bold;color:#1A3C2A;background:transparent;")
        v.addWidget(sec_title)

        form = QGridLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        # Tanggal
        form.addWidget(self._form_label("Tanggal"), 0, 0)
        self.date_edit = QDateEdit()
        self.date_edit.setDate(date.today())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setStyleSheet(self._input_style())
        form.addWidget(self.date_edit, 0, 1)

        # Nominal
        form.addWidget(self._form_label("Nominal (Rp)"), 1, 0)
        self.nominal_input = QLineEdit()
        self.nominal_input.setPlaceholderText("Contoh: 50000")
        self.nominal_input.setValidator(QIntValidator(0, 999_999_999))
        self.nominal_input.setStyleSheet(self._input_style())
        form.addWidget(self.nominal_input, 1, 1)

        # Kategori
        form.addWidget(self._form_label("Kategori"), 2, 0)
        self.kategori_combo = QComboBox()
        self.kategori_combo.addItems(KATEGORI_SEDEKAH)
        self.kategori_combo.setStyleSheet(self._combo_style())
        form.addWidget(self.kategori_combo, 2, 1)

        # Keterangan
        form.addWidget(self._form_label("Keterangan"), 3, 0)
        self.keterangan_input = QLineEdit()
        self.keterangan_input.setPlaceholderText("Opsional")
        self.keterangan_input.setStyleSheet(self._input_style())
        form.addWidget(self.keterangan_input, 3, 1)

        v.addLayout(form)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        save_btn = QPushButton("Simpan Sedekah")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background:#2D6B4A; color:#FFF; font-size:13px;
                font-weight:bold; border:none; border-radius:12px;
                padding:10px 24px;
            }
            QPushButton:hover { background:#1A3C2A; }
        """)
        save_btn.clicked.connect(self._save_sedekah)
        btn_row.addWidget(save_btn)
        btn_row.addStretch()

        v.addLayout(btn_row)

        # ── Target Bulanan ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:#E4E8DE;max-height:1px;border:none;")
        v.addWidget(sep)

        tgt_title = QLabel("Target Sedekah Bulanan")
        tgt_title.setStyleSheet("font-size:14px;font-weight:bold;color:#1A3C2A;background:transparent;")
        v.addWidget(tgt_title)

        tgt_row = QHBoxLayout()
        tgt_row.setSpacing(10)
        lbl = QLabel("Target Rp:")
        lbl.setStyleSheet("font-size:12px;color:#555;background:transparent;")
        tgt_row.addWidget(lbl)
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Contoh: 500000")
        self.target_input.setValidator(QIntValidator(0, 999_999_999))
        self.target_input.setFixedWidth(180)
        self.target_input.setStyleSheet(self._input_style())
        tgt_row.addWidget(self.target_input)

        # Month/year for target
        self.target_bulan = QComboBox()
        for i in range(1, 13):
            self.target_bulan.addItem(
                date(2000, i, 1).strftime("%B"), i)
        self.target_bulan.setCurrentIndex(date.today().month - 1)
        self.target_bulan.setStyleSheet(self._combo_style())
        self.target_bulan.setFixedWidth(120)
        tgt_row.addWidget(self.target_bulan)

        self.target_tahun = QSpinBox()
        self.target_tahun.setRange(2020, 2040)
        self.target_tahun.setValue(date.today().year)
        self.target_tahun.setStyleSheet(
            "QSpinBox{border:1px solid #D0D5CC;border-radius:8px;padding:6px 10px;"
            "font-size:12px;background:#FAFBF8;}")
        self.target_tahun.setFixedWidth(90)
        tgt_row.addWidget(self.target_tahun)

        tgt_save = QPushButton("Set Target")
        tgt_save.setCursor(Qt.CursorShape.PointingHandCursor)
        tgt_save.setStyleSheet("""
            QPushButton{background:#2D6B4A;color:#FFF;font-size:12px;font-weight:bold;
            border:none;border-radius:10px;padding:8px 18px;}
            QPushButton:hover{background:#1A3C2A;}""")
        tgt_save.clicked.connect(self._save_target)
        tgt_row.addWidget(tgt_save)
        tgt_row.addStretch()
        v.addLayout(tgt_row)

        return card

    # ═══════════════════════════════════════════
    #  SECTION 2: PROGRESS BAR
    # ═══════════════════════════════════════════
    def _build_progress_section(self):
        card = QFrame()
        card.setObjectName("progressCard")
        card.setStyleSheet("""
            QFrame#progressCard {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #1A3C2A, stop:1 #2D6B4A);
                border-radius: 16px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16); shadow.setColor(QColor(0, 0, 0, 25)); shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(8)

        # month nav row
        nav_row = QHBoxLayout()
        prev_btn = QPushButton("◀")
        prev_btn.setFixedSize(28, 28)
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,15);color:#FFF;border:none;"
            "border-radius:14px;font-size:14px;}"
            "QPushButton:hover{background:rgba(255,255,255,25);}")
        prev_btn.clicked.connect(self._prev_month)
        nav_row.addWidget(prev_btn)

        self.progress_month_label = QLabel("")
        self.progress_month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_month_label.setStyleSheet(
            "font-size:16px;font-weight:bold;color:#FFF;background:transparent;")
        nav_row.addWidget(self.progress_month_label, 1)

        next_btn = QPushButton("▶")
        next_btn.setFixedSize(28, 28)
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,15);color:#FFF;border:none;"
            "border-radius:14px;font-size:14px;}"
            "QPushButton:hover{background:rgba(255,255,255,25);}")
        next_btn.clicked.connect(self._next_month)
        nav_row.addWidget(next_btn)
        v.addLayout(nav_row)

        # Progress info
        self.progress_total_label = QLabel("Total: Rp 0")
        self.progress_total_label.setStyleSheet(
            "font-size:22px;font-weight:bold;color:#FFD88E;background:transparent;")
        v.addWidget(self.progress_total_label)

        self.progress_target_label = QLabel("Target: Belum diatur")
        self.progress_target_label.setStyleSheet(
            "font-size:12px;color:rgba(255,255,255,170);background:transparent;")
        v.addWidget(self.progress_target_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("""
            QProgressBar{background:rgba(255,255,255,20);border:none;border-radius:6px;}
            QProgressBar::chunk{background:#FFD88E;border-radius:6px;}""")
        v.addWidget(self.progress_bar)

        self.progress_pct_label = QLabel("")
        self.progress_pct_label.setStyleSheet(
            "font-size:12px;color:rgba(255,255,255,180);background:transparent;")
        v.addWidget(self.progress_pct_label)

        return card

    # ═══════════════════════════════════════════
    #  SECTION 3: HIJRI CALENDAR
    # ═══════════════════════════════════════════
    def _build_calendar_section(self):
        card = QFrame()
        card.setObjectName("calCard")
        card.setStyleSheet("""
            QFrame#calCard {
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid rgba(0,0,0,6);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16); shadow.setColor(QColor(0, 0, 0, 15)); shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(10)

        cal_title = QLabel("Kalender Sedekah (Hijriyah)")
        cal_title.setStyleSheet("font-size:16px;font-weight:bold;color:#1A3C2A;background:transparent;")
        v.addWidget(cal_title)

        self.hijri_month_label = QLabel("")
        self.hijri_month_label.setStyleSheet("font-size:13px;color:#777;background:transparent;")
        v.addWidget(self.hijri_month_label)

        # Day-of-week header
        dow_row = QHBoxLayout()
        dow_row.setSpacing(4)
        for d in HARI_NAMES:
            lbl = QLabel(d)
            lbl.setFixedSize(40, 24)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size:11px;font-weight:bold;color:#999;background:transparent;")
            dow_row.addWidget(lbl)
        dow_row.addStretch()
        v.addLayout(dow_row)

        # Calendar grid container
        self.cal_grid_widget = QWidget()
        self.cal_grid_widget.setStyleSheet("background:transparent;")
        self.cal_grid_layout = QGridLayout(self.cal_grid_widget)
        self.cal_grid_layout.setSpacing(4)
        self.cal_grid_layout.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.cal_grid_widget)

        # Legend
        leg = QHBoxLayout()
        leg.setSpacing(16)
        for color, text in [("#2D6B4A", "Sudah sedekah"), ("#E4E8DE", "Belum"), ("#FFD88E", "Hari ini")]:
            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"background:{color};border-radius:6px;")
            leg.addWidget(dot)
            lt = QLabel(text)
            lt.setStyleSheet("font-size:11px;color:#888;background:transparent;")
            leg.addWidget(lt)
        leg.addStretch()
        v.addLayout(leg)

        return card

    # ═══════════════════════════════════════════
    #  SECTION 4: RIWAYAT SEDEKAH
    # ═══════════════════════════════════════════
    def _build_history_section(self):
        card = QFrame()
        card.setObjectName("histCard")
        card.setStyleSheet("""
            QFrame#histCard {
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid rgba(0,0,0,6);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16); shadow.setColor(QColor(0, 0, 0, 15)); shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(6)

        t = QLabel("Riwayat Sedekah Bulan Ini")
        t.setStyleSheet("font-size:16px;font-weight:bold;color:#1A3C2A;background:transparent;")
        v.addWidget(t)

        self.history_container = QWidget()
        self.history_container.setStyleSheet("background:transparent;")
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(0, 4, 0, 0)
        self.history_layout.setSpacing(4)
        v.addWidget(self.history_container)

        return card

    # ═══════════════════════════════════════════
    #  STYLE HELPERS
    # ═══════════════════════════════════════════
    def _form_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size:12px;color:#555;font-weight:bold;background:transparent;")
        lbl.setFixedWidth(110)
        return lbl

    @staticmethod
    def _input_style():
        return ("QLineEdit, QDateEdit {"
                "border:1px solid #D0D5CC;border-radius:8px;padding:8px 12px;"
                "font-size:13px;background:#FAFBF8;color:#333;}"
                "QLineEdit:focus, QDateEdit:focus {border-color:#2D6B4A;}")

    @staticmethod
    def _combo_style():
        return ("QComboBox{border:1px solid #D0D5CC;border-radius:8px;padding:8px 12px;"
                "font-size:12px;background:#FAFBF8;color:#333;}"
                "QComboBox:focus{border-color:#2D6B4A;}"
                "QComboBox::drop-down{border:none;width:24px;}"
                "QComboBox QAbstractItemView{background:#FFF;border:1px solid #DDD;"
                "selection-background-color:#EAF5E6;selection-color:#333;}")

    # ═══════════════════════════════════════════
    #  ACTIONS
    # ═══════════════════════════════════════════
    def _save_sedekah(self):
        if not self.user_id:
            return
        nom_text = self.nominal_input.text().strip()
        if not nom_text:
            QMessageBox.warning(self, "Peringatan", "Nominal tidak boleh kosong.")
            return
        nominal = int(nom_text)
        if nominal <= 0:
            QMessageBox.warning(self, "Peringatan", "Nominal harus lebih dari 0.")
            return

        tanggal = self.date_edit.date().toString("yyyy-MM-dd")
        kategori = self.kategori_combo.currentText()
        keterangan = self.keterangan_input.text().strip()

        self.db.add_sedekah(self.user_id, tanggal, nominal, kategori, keterangan)

        # Reset form
        self.nominal_input.clear()
        self.keterangan_input.clear()
        self.date_edit.setDate(date.today())

        self._refresh_all()

    def _save_target(self):
        if not self.user_id:
            return
        tgt_text = self.target_input.text().strip()
        if not tgt_text:
            QMessageBox.warning(self, "Peringatan", "Target nominal tidak boleh kosong.")
            return
        target = int(tgt_text)
        if target <= 0:
            QMessageBox.warning(self, "Peringatan", "Target harus lebih dari 0.")
            return
        bulan = self.target_bulan.currentData()
        tahun = self.target_tahun.value()
        self.db.set_sedekah_target(self.user_id, bulan, tahun, target)
        self.target_input.clear()
        self._refresh_all()

    def _prev_month(self):
        if self._view_month == 1:
            self._view_month = 12
            self._view_year -= 1
        else:
            self._view_month -= 1
        self._refresh_all()

    def _next_month(self):
        if self._view_month == 12:
            self._view_month = 1
            self._view_year += 1
        else:
            self._view_month += 1
        self._refresh_all()

    def _delete_sedekah(self, sedekah_id):
        self.db.delete_sedekah(sedekah_id)
        self._refresh_all()

    # ═══════════════════════════════════════════
    #  REFRESH ALL SECTIONS
    # ═══════════════════════════════════════════
    def _refresh_all(self):
        if not self.user_id:
            return
        self._refresh_progress()
        self._refresh_calendar()
        self._refresh_history()

    def _refresh_progress(self):
        m, y = self._view_month, self._view_year
        total = self.db.get_total_sedekah_bulan(self.user_id, m, y)
        target_row = self.db.get_sedekah_target(self.user_id, m, y)

        month_name = date(y, m, 1).strftime("%B %Y")
        self.progress_month_label.setText(month_name)
        self.progress_total_label.setText(f"Total: {_format_rupiah(total)}")

        if target_row:
            tgt = target_row["target_nominal"]
            self.progress_target_label.setText(f"Target: {_format_rupiah(tgt)}")
            pct = min(100, int(total / tgt * 100)) if tgt > 0 else 0
            self.progress_bar.setValue(pct)
            self.progress_pct_label.setText(f"{pct}% tercapai")
        else:
            self.progress_target_label.setText("Target: Belum diatur")
            self.progress_bar.setValue(0)
            self.progress_pct_label.setText("")

    def _refresh_calendar(self):
        m, y = self._view_month, self._view_year

        # Get sedekah days (set of date strings)
        sedekah_days = set(self.db.get_sedekah_days(self.user_id, m, y))
        today_str = date.today().isoformat()

        # Hijri info for the 1st of the viewed month
        h_y, h_m, h_d = gregorian_to_hijri(y, m, 1)
        self.hijri_month_label.setText(
            f"≈ {HIJRI_MONTH_NAMES[h_m]} {h_y} H  ·  {date(y, m, 1).strftime('%B %Y')}")

        # Clear grid
        while self.cal_grid_layout.count():
            item = self.cal_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build calendar days
        import calendar
        cal = calendar.Calendar(firstweekday=0)  # Monday first
        row = 0
        for d in cal.itermonthdays(y, m):
            if d == 0:
                continue
            dt = date(y, m, d)
            dow = dt.weekday()  # 0=Mon
            if d == 1:
                row = 0
            elif dow == 0 and d > 1:
                row += 1

            day_str = dt.isoformat()
            has_sedekah = day_str in sedekah_days
            is_today = day_str == today_str

            cell = QLabel(str(d))
            cell.setFixedSize(40, 36)
            cell.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if is_today:
                cell.setStyleSheet(
                    "background:#FFD88E;color:#1A3C2A;font-size:12px;font-weight:bold;"
                    "border-radius:10px;")
            elif has_sedekah:
                cell.setStyleSheet(
                    "background:#2D6B4A;color:#FFF;font-size:12px;font-weight:bold;"
                    "border-radius:10px;")
            else:
                cell.setStyleSheet(
                    "background:#F0F2EC;color:#777;font-size:12px;"
                    "border-radius:10px;")

            # Show hijri day below
            h_y2, h_m2, h_d2 = gregorian_to_hijri(y, m, d)
            hijri_sub = QLabel(str(h_d2))
            hijri_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hijri_sub.setStyleSheet("font-size:8px;color:#aaa;background:transparent;")

            container = QWidget()
            container.setStyleSheet("background:transparent;")
            cv = QVBoxLayout(container)
            cv.setContentsMargins(0, 0, 0, 0)
            cv.setSpacing(0)
            cv.addWidget(cell)
            cv.addWidget(hijri_sub)

            self.cal_grid_layout.addWidget(container, row, dow)

    def _refresh_history(self):
        m, y = self._view_month, self._view_year
        records = self.db.get_sedekah_bulan(self.user_id, m, y)

        # Clear
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not records:
            empty = QLabel("Belum ada catatan sedekah bulan ini.")
            empty.setStyleSheet("font-size:13px;color:#999;background:transparent;padding:12px 0;")
            self.history_layout.addWidget(empty)
            return

        for rec in reversed(records):  # newest first
            row = QFrame()
            row.setFixedHeight(52)
            row.setStyleSheet("""
                QFrame {
                    background: #FAFBF8;
                    border-radius: 10px;
                    border: 1px solid rgba(0,0,0,4);
                }
            """)
            h = QHBoxLayout(row)
            h.setContentsMargins(14, 0, 14, 0)
            h.setSpacing(12)

            # Kategori badge
            badge = QLabel(rec["kategori"][:3].upper())
            badge.setFixedSize(38, 38)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                "background:#EAF5E6;color:#2D6B4A;font-size:10px;"
                "font-weight:bold;border-radius:19px;")
            h.addWidget(badge)

            # Info
            info_v = QVBoxLayout()
            info_v.setSpacing(2)
            kat_lbl = QLabel(rec["kategori"])
            kat_lbl.setStyleSheet("font-size:13px;font-weight:bold;color:#333;background:transparent;")
            info_v.addWidget(kat_lbl)
            try:
                dt_obj = datetime.strptime(rec["tanggal"], "%Y-%m-%d")
                date_str = dt_obj.strftime("%d %b %Y")
            except ValueError:
                date_str = rec["tanggal"]
            ket = rec.get("keterangan", "")
            sub_text = date_str + (f" · {ket}" if ket else "")
            sub = QLabel(sub_text)
            sub.setStyleSheet("font-size:11px;color:#999;background:transparent;")
            info_v.addWidget(sub)
            h.addLayout(info_v, 1)

            # Nominal
            nom = QLabel(_format_rupiah(rec["nominal"]))
            nom.setStyleSheet("font-size:14px;font-weight:bold;color:#2D6B4A;background:transparent;")
            h.addWidget(nom)

            # Delete
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(26, 26)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet(
                "QPushButton{background:transparent;color:#CCC;border:none;font-size:14px;}"
                "QPushButton:hover{color:#E74C3C;}")
            del_btn.clicked.connect(lambda _, sid=rec["id"]: self._delete_sedekah(sid))
            h.addWidget(del_btn)

            self.history_layout.addWidget(row)
