"""
Settings Page - AMALY
Ubah nama, password, ukuran teks Arab, lokasi.
"""

import os
import threading
import requests

from PyQt6.QtCore import Qt, pyqtSignal, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QColor, QPixmap, QFont
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QScrollArea, QSlider,
    QVBoxLayout, QWidget,
)

from ui_dashboard import IconWidget

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_SHALAT = "https://equran.id/api/v2/shalat"


class SettingsPage(QWidget):
    back_to_dashboard = pyqtSignal()
    logout_signal = pyqtSignal()
    arab_size_changed = pyqtSignal(int)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = None
        self.user_data = None
        self._provinsi_list = []
        self._kabkota_list = []
        self.setup_ui()

    def set_user_data(self, data):
        if not data:
            return
        self.user_data = data
        self.user_id = data.get("id")
        self.name_input.setText(data.get("nama_lengkap", ""))

        # Load saved arab text size
        saved_size = self.db.get_setting(self.user_id, "arab_font_size", "24")
        self.arab_size_slider.setValue(int(saved_size))
        self._update_size_preview(int(saved_size))

        # Set current location info
        prov = data.get("provinsi", "")
        kab = data.get("kabkota", "")
        loc_text = f"{kab}, {prov}" if kab and prov else prov or kab or "Belum diatur"
        self.current_loc_label.setText(f"Lokasi saat ini: {loc_text}")

        self._load_provinsi()

    # ─────────────── ROOT ───────────────
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
        settings_btn = self._sidebar_btn("gear", "Settings", True)
        lay.addWidget(settings_btn)
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

    # ─────────────── CONTENT ───────────────
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
        col.setSpacing(18)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet("font-size:24px;font-weight:bold;color:#1A3C2A;background:transparent;")
        col.addWidget(title)

        # 1. Change Name
        col.addWidget(self._build_name_card())
        # 2. Change Password
        col.addWidget(self._build_password_card())
        # 3. Arab text size
        col.addWidget(self._build_textsize_card())
        # 4. Change Location
        col.addWidget(self._build_location_card())
        # Logout
        col.addWidget(self._build_logout_card())

        col.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return wrapper

    # ═══════════════════════════════════════════
    #  CARD 1: UBAH NAMA
    # ═══════════════════════════════════════════
    def _build_name_card(self):
        card = self._card_frame()
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(10)

        v.addWidget(self._section_title("Ubah Nama"))

        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = QLabel("Nama Lengkap:")
        lbl.setFixedWidth(120)
        lbl.setStyleSheet("font-size:13px;color:#555;background:transparent;")
        row.addWidget(lbl)
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(self._input_style())
        self.name_input.setPlaceholderText("Nama lengkap baru")
        row.addWidget(self.name_input, 1)

        save_btn = self._action_btn("Simpan Nama")
        save_btn.clicked.connect(self._save_name)
        row.addWidget(save_btn)
        v.addLayout(row)

        self.name_msg = QLabel("")
        self.name_msg.setStyleSheet("font-size:11px;background:transparent;")
        v.addWidget(self.name_msg)
        return card

    # ═══════════════════════════════════════════
    #  CARD 2: GANTI PASSWORD
    # ═══════════════════════════════════════════
    def _build_password_card(self):
        card = self._card_frame()
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(10)

        v.addWidget(self._section_title("Ganti Password"))

        # Old password
        r1 = QHBoxLayout()
        r1.setSpacing(12)
        lbl1 = QLabel("Password Lama:")
        lbl1.setFixedWidth(120)
        lbl1.setStyleSheet("font-size:13px;color:#555;background:transparent;")
        r1.addWidget(lbl1)
        self.old_pw_input = QLineEdit()
        self.old_pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_pw_input.setStyleSheet(self._input_style())
        r1.addWidget(self.old_pw_input, 1)
        v.addLayout(r1)

        # New password
        r2 = QHBoxLayout()
        r2.setSpacing(12)
        lbl2 = QLabel("Password Baru:")
        lbl2.setFixedWidth(120)
        lbl2.setStyleSheet("font-size:13px;color:#555;background:transparent;")
        r2.addWidget(lbl2)
        self.new_pw_input = QLineEdit()
        self.new_pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pw_input.setStyleSheet(self._input_style())
        r2.addWidget(self.new_pw_input, 1)
        v.addLayout(r2)

        # Confirm password
        r3 = QHBoxLayout()
        r3.setSpacing(12)
        lbl3 = QLabel("Konfirmasi:")
        lbl3.setFixedWidth(120)
        lbl3.setStyleSheet("font-size:13px;color:#555;background:transparent;")
        r3.addWidget(lbl3)
        self.confirm_pw_input = QLineEdit()
        self.confirm_pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pw_input.setStyleSheet(self._input_style())
        r3.addWidget(self.confirm_pw_input, 1)
        v.addLayout(r3)

        btn_row = QHBoxLayout()
        save_pw_btn = self._action_btn("Ganti Password")
        save_pw_btn.clicked.connect(self._save_password)
        btn_row.addWidget(save_pw_btn)
        btn_row.addStretch()
        v.addLayout(btn_row)

        self.pw_msg = QLabel("")
        self.pw_msg.setStyleSheet("font-size:11px;background:transparent;")
        v.addWidget(self.pw_msg)
        return card

    # ═══════════════════════════════════════════
    #  CARD 3: UKURAN TEKS ARAB
    # ═══════════════════════════════════════════
    def _build_textsize_card(self):
        card = self._card_frame()
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(10)

        v.addWidget(self._section_title("Ukuran Teks Arab Al-Qur'an"))

        row = QHBoxLayout()
        row.setSpacing(14)
        small_lbl = QLabel("Kecil")
        small_lbl.setStyleSheet("font-size:11px;color:#999;background:transparent;")
        row.addWidget(small_lbl)

        self.arab_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.arab_size_slider.setMinimum(16)
        self.arab_size_slider.setMaximum(42)
        self.arab_size_slider.setValue(24)
        self.arab_size_slider.setTickInterval(2)
        self.arab_size_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #E4E8DE; height: 6px; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #2D6B4A; width: 18px; height: 18px;
                margin: -6px 0; border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #2D6B4A; border-radius: 3px;
            }
        """)
        self.arab_size_slider.valueChanged.connect(self._on_size_changed)
        row.addWidget(self.arab_size_slider, 1)

        big_lbl = QLabel("Besar")
        big_lbl.setStyleSheet("font-size:11px;color:#999;background:transparent;")
        row.addWidget(big_lbl)

        self.size_value_label = QLabel("24px")
        self.size_value_label.setFixedWidth(50)
        self.size_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_value_label.setStyleSheet(
            "font-size:13px;font-weight:bold;color:#2D6B4A;background:#EAF5E6;"
            "border-radius:8px;padding:4px;")
        row.addWidget(self.size_value_label)
        v.addLayout(row)

        # Preview
        self.arab_preview = QLabel("بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ")
        self.arab_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.arab_preview.setWordWrap(True)
        self.arab_preview.setStyleSheet(
            "font-size:24px;color:#1A3C2A;background:#FAFBF8;"
            "border-radius:12px;padding:16px;border:1px solid rgba(0,0,0,5);")
        self.arab_preview.setFont(QFont("Traditional Arabic", 24))
        v.addWidget(self.arab_preview)

        return card

    # ═══════════════════════════════════════════
    #  CARD 4: UBAH LOKASI
    # ═══════════════════════════════════════════
    def _build_location_card(self):
        card = self._card_frame()
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(10)

        v.addWidget(self._section_title("Ubah Lokasi"))

        self.current_loc_label = QLabel("Lokasi saat ini: -")
        self.current_loc_label.setStyleSheet(
            "font-size:12px;color:#777;background:transparent;font-style:italic;")
        v.addWidget(self.current_loc_label)

        # Provinsi
        r1 = QHBoxLayout()
        r1.setSpacing(12)
        lbl1 = QLabel("Provinsi:")
        lbl1.setFixedWidth(120)
        lbl1.setStyleSheet("font-size:13px;color:#555;background:transparent;")
        r1.addWidget(lbl1)
        self.provinsi_combo = QComboBox()
        self.provinsi_combo.addItem("Memuat provinsi...")
        self.provinsi_combo.setStyleSheet(self._combo_style())
        self.provinsi_combo.currentIndexChanged.connect(self._on_provinsi_changed)
        r1.addWidget(self.provinsi_combo, 1)
        v.addLayout(r1)

        # Kabkota
        r2 = QHBoxLayout()
        r2.setSpacing(12)
        lbl2 = QLabel("Kabupaten/Kota:")
        lbl2.setFixedWidth(120)
        lbl2.setStyleSheet("font-size:13px;color:#555;background:transparent;")
        r2.addWidget(lbl2)
        self.kabkota_combo = QComboBox()
        self.kabkota_combo.addItem("Pilih provinsi dahulu")
        self.kabkota_combo.setEnabled(False)
        self.kabkota_combo.setStyleSheet(self._combo_style())
        r2.addWidget(self.kabkota_combo, 1)
        v.addLayout(r2)

        btn_row = QHBoxLayout()
        save_loc_btn = self._action_btn("Simpan Lokasi")
        save_loc_btn.clicked.connect(self._save_location)
        btn_row.addWidget(save_loc_btn)
        btn_row.addStretch()
        v.addLayout(btn_row)

        self.loc_msg = QLabel("")
        self.loc_msg.setStyleSheet("font-size:11px;background:transparent;")
        v.addWidget(self.loc_msg)
        return card

    # ═══════════════════════════════════════════
    #  LOGOUT CARD
    # ═══════════════════════════════════════════
    def _build_logout_card(self):
        card = self._card_frame()
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(10)

        logout_btn = QPushButton("Logout")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background:#E74C3C; color:#FFF; font-size:14px;
                font-weight:bold; border:none; border-radius:12px;
                padding:12px 32px;
            }
            QPushButton:hover { background:#C0392B; }
        """)
        logout_btn.clicked.connect(self.logout_signal.emit)
        v.addWidget(logout_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        return card

    # ═══════════════════════════════════════════
    #  STYLE HELPERS
    # ═══════════════════════════════════════════
    def _card_frame(self):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid rgba(0,0,0,6);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)
        return card

    def _section_title(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size:16px;font-weight:bold;color:#1A3C2A;background:transparent;")
        return lbl

    def _action_btn(self, text):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background:#2D6B4A; color:#FFF; font-size:12px;
                font-weight:bold; border:none; border-radius:10px;
                padding:8px 20px;
            }
            QPushButton:hover { background:#1A3C2A; }
        """)
        return btn

    @staticmethod
    def _input_style():
        return ("QLineEdit {"
                "border:1px solid #D0D5CC;border-radius:8px;padding:8px 12px;"
                "font-size:13px;background:#FAFBF8;color:#333;}"
                "QLineEdit:focus {border-color:#2D6B4A;}")

    @staticmethod
    def _combo_style():
        return ("QComboBox{border:1px solid #D0D5CC;border-radius:8px;padding:8px 12px;"
            "font-size:12px;background:#FAFBF8;color:#000;}"
            "QComboBox:focus{border-color:#2D6B4A;}"
            "QComboBox::drop-down{border:none;width:24px;}"
            "QComboBox QAbstractItemView{background:#FFF;border:1px solid #DDD;"
            "selection-background-color:#EAF5E6;selection-color:#000;}"
            "QComboBox QAbstractItemView::item{color:#000;}"
            "QComboBox QAbstractItemView::item:selected{color:#000;background:#EAF5E6;}")

    def _show_msg(self, label, text, success=True):
        color = "#2D6B4A" if success else "#E74C3C"
        label.setStyleSheet(f"font-size:11px;color:{color};background:transparent;")
        label.setText(text)

    # ═══════════════════════════════════════════
    #  ACTIONS
    # ═══════════════════════════════════════════
    def _save_name(self):
        if not self.user_id:
            return
        new_name = self.name_input.text().strip()
        if not new_name:
            self._show_msg(self.name_msg, "Nama tidak boleh kosong.", False)
            return
        ok, msg = self.db.update_user_name(self.user_id, new_name)
        self._show_msg(self.name_msg, msg, ok)
        if ok and self.user_data:
            self.user_data["nama_lengkap"] = new_name
            self.user_data["username"] = new_name.strip().lower().replace(' ', '_')

    def _save_password(self):
        if not self.user_id:
            return
        old_pw = self.old_pw_input.text()
        new_pw = self.new_pw_input.text()
        confirm = self.confirm_pw_input.text()

        if not old_pw or not new_pw:
            self._show_msg(self.pw_msg, "Semua field harus diisi.", False)
            return
        if len(new_pw) < 4:
            self._show_msg(self.pw_msg, "Password baru minimal 4 karakter.", False)
            return
        if new_pw != confirm:
            self._show_msg(self.pw_msg, "Konfirmasi password tidak cocok.", False)
            return

        ok, msg = self.db.update_user_password(self.user_id, old_pw, new_pw)
        self._show_msg(self.pw_msg, msg, ok)
        if ok:
            self.old_pw_input.clear()
            self.new_pw_input.clear()
            self.confirm_pw_input.clear()

    def _on_size_changed(self, value):
        if not self.user_id:
            return
        self._update_size_preview(value)
        self.db.set_setting(self.user_id, "arab_font_size", str(value))
        self.arab_size_changed.emit(value)

    def _update_size_preview(self, size):
        self.size_value_label.setText(f"{size}px")
        self.arab_preview.setStyleSheet(
            f"font-size:{size}px;color:#1A3C2A;background:#FAFBF8;"
            f"border-radius:12px;padding:16px;border:1px solid rgba(0,0,0,5);")
        self.arab_preview.setFont(QFont("Traditional Arabic", size))

    def _save_location(self):
        if not self.user_id:
            return
        if self.provinsi_combo.currentIndex() <= 0:
            self._show_msg(self.loc_msg, "Pilih provinsi terlebih dahulu.", False)
            return
        if self.kabkota_combo.currentIndex() <= 0 or not self.kabkota_combo.isEnabled():
            self._show_msg(self.loc_msg, "Pilih kabupaten/kota terlebih dahulu.", False)
            return

        provinsi = self.provinsi_combo.currentText()
        kabkota = self.kabkota_combo.currentText()
        self.db.update_user_location(self.user_id, provinsi, kabkota)

        if self.user_data:
            self.user_data["provinsi"] = provinsi
            self.user_data["kabkota"] = kabkota
            self.user_data["location"] = f"{kabkota}, {provinsi}"

        self.current_loc_label.setText(f"Lokasi saat ini: {kabkota}, {provinsi}")
        self._show_msg(self.loc_msg, "Lokasi berhasil diubah.", True)

    # ═══════════════════════════════════════════
    #  API: PROVINSI / KABKOTA
    # ═══════════════════════════════════════════
    def _load_provinsi(self):
        def fetch():
            try:
                r = requests.get(f"{API_SHALAT}/provinsi", timeout=10)
                data = r.json().get("data", [])
                QMetaObject.invokeMethod(
                    self, "_set_provinsi_list",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(list, data))
            except Exception:
                QMetaObject.invokeMethod(
                    self, "_set_provinsi_list",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(list, []))
        threading.Thread(target=fetch, daemon=True).start()

    @pyqtSlot(list)
    def _set_provinsi_list(self, data):
        self._provinsi_list = data
        self.provinsi_combo.blockSignals(True)
        self.provinsi_combo.clear()
        if data:
            self.provinsi_combo.addItem("Pilih provinsi...")
            for prov in data:
                self.provinsi_combo.addItem(prov)
            # Pre-select current provinsi
            if self.user_data:
                cur = self.user_data.get("provinsi", "")
                idx = self.provinsi_combo.findText(cur)
                if idx >= 0:
                    self.provinsi_combo.setCurrentIndex(idx)
        else:
            self.provinsi_combo.addItem("Gagal memuat provinsi")
        self.provinsi_combo.blockSignals(False)
        # Trigger kabkota load if provinsi pre-selected
        if self.provinsi_combo.currentIndex() > 0:
            self._on_provinsi_changed(self.provinsi_combo.currentIndex())

    def _on_provinsi_changed(self, index):
        self.kabkota_combo.clear()
        if index <= 0 or not self._provinsi_list:
            self.kabkota_combo.addItem("Pilih provinsi dahulu")
            self.kabkota_combo.setEnabled(False)
            return
        provinsi = self.provinsi_combo.currentText()
        self.kabkota_combo.addItem("Memuat kabupaten/kota...")
        self.kabkota_combo.setEnabled(False)

        def fetch():
            try:
                r = requests.post(
                    f"{API_SHALAT}/kabkota",
                    json={"provinsi": provinsi}, timeout=10)
                data = r.json().get("data", [])
                QMetaObject.invokeMethod(
                    self, "_set_kabkota_list",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(list, data))
            except Exception:
                QMetaObject.invokeMethod(
                    self, "_set_kabkota_list",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(list, []))
        threading.Thread(target=fetch, daemon=True).start()

    @pyqtSlot(list)
    def _set_kabkota_list(self, data):
        self._kabkota_list = data
        self.kabkota_combo.clear()
        if data:
            self.kabkota_combo.addItem("Pilih kabupaten/kota...")
            for kab in data:
                self.kabkota_combo.addItem(kab)
            self.kabkota_combo.setEnabled(True)
            # Pre-select current kabkota
            if self.user_data:
                cur = self.user_data.get("kabkota", "")
                idx = self.kabkota_combo.findText(cur)
                if idx >= 0:
                    self.kabkota_combo.setCurrentIndex(idx)
        else:
            self.kabkota_combo.addItem("Gagal memuat data")
            self.kabkota_combo.setEnabled(False)
