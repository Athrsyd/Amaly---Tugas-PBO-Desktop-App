"""
Register Page - AMALY - Glassmorphism Design
Matches: CREATE ACCOUNT centered card with full background image
"""

import os
import threading
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QSizePolicy, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QMetaObject, Q_ARG
from PyQt6.QtGui import QPixmap, QColor, QPainter, QLinearGradient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class RegisterPage(QWidget):
    """Halaman Create Account - Glassmorphism centered card"""

    switch_to_login = pyqtSignal()
    register_success = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.bg_pixmap = None
        self._provinsi_list = []
        self._kabkota_list = []
        self._load_background()
        self.setup_ui()
        self._load_provinsi()

    def _load_background(self):
        for name in ("BG-Auth.jpg", "BG-Auth.png", "Rectangle 2.png"):
            bg_path = os.path.join(BASE_DIR, name)
            if os.path.exists(bg_path):
                self.bg_pixmap = QPixmap(bg_path)
                return

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            scaled = self.bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(20, 55, 35))
            gradient.setColorAt(0.5, QColor(35, 75, 55))
            gradient.setColorAt(1, QColor(15, 45, 30))
            painter.fillRect(self.rect(), gradient)
        painter.end()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ==================== GLASS CARD ====================
        card = QFrame()
        card.setFixedSize(400, 640)
        card.setObjectName("glassCard")
        card.setStyleSheet("""
            QFrame#glassCard {
                background-color: rgba(55, 85, 65, 160);
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 28);
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(45, 32, 45, 18)
        card_layout.setSpacing(0)

        # ---- Title: CREATE ACCOUNT ----
        title = QLabel("CREATE ACCOUNT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
                letter-spacing: 1px;
            }
        """)
        card_layout.addWidget(title)
        card_layout.addSpacing(22)

        # ---- Name Field ----
        name_label = QLabel("Name")
        name_label.setStyleSheet(self._label_style())
        card_layout.addWidget(name_label)
        card_layout.addSpacing(4)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your full name")
        self.name_input.setMinimumHeight(42)
        self.name_input.setStyleSheet(self._input_style())
        card_layout.addWidget(self.name_input)
        card_layout.addSpacing(12)

        # ---- Provinsi Dropdown ----
        prov_label = QLabel("Provinsi")
        prov_label.setStyleSheet(self._label_style())
        card_layout.addWidget(prov_label)
        card_layout.addSpacing(4)

        self.provinsi_combo = QComboBox()
        self.provinsi_combo.addItem("Memuat provinsi...")
        self.provinsi_combo.setMinimumHeight(42)
        self.provinsi_combo.setStyleSheet(self._combo_style())
        self.provinsi_combo.currentIndexChanged.connect(self._on_provinsi_changed)
        card_layout.addWidget(self.provinsi_combo)
        card_layout.addSpacing(12)

        # ---- Kabupaten/Kota Dropdown ----
        kab_label = QLabel("Kabupaten / Kota")
        kab_label.setStyleSheet(self._label_style())
        card_layout.addWidget(kab_label)
        card_layout.addSpacing(4)

        self.kabkota_combo = QComboBox()
        self.kabkota_combo.addItem("Pilih provinsi dahulu")
        self.kabkota_combo.setMinimumHeight(42)
        self.kabkota_combo.setStyleSheet(self._combo_style())
        self.kabkota_combo.setEnabled(False)
        card_layout.addWidget(self.kabkota_combo)
        card_layout.addSpacing(12)

        # ---- Password Field ----
        pw_label = QLabel("Password")
        pw_label.setStyleSheet(self._label_style())
        card_layout.addWidget(pw_label)
        card_layout.addSpacing(4)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(42)
        self.password_input.setStyleSheet(self._input_style())
        self.password_input.returnPressed.connect(self.handle_register)
        card_layout.addWidget(self.password_input)
        card_layout.addSpacing(4)

        # ---- Error / Success Label ----
        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("color: #FF6B6B; font-size: 11px; background: transparent;")
        self.message_label.setVisible(False)
        self.message_label.setFixedHeight(16)
        card_layout.addWidget(self.message_label)
        card_layout.addSpacing(8)

        # ---- SIGN UP Button ----
        signup_btn = QPushButton("SIGN UP")
        signup_btn.setMinimumHeight(50)
        signup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        signup_btn.setStyleSheet("""
            QPushButton {
                background-color: #1B4332;
                color: #FFFFFF;
                border: none;
                border-radius: 25px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 3px;
            }
            QPushButton:hover { background-color: #245639; }
            QPushButton:pressed { background-color: #143326; }
        """)
        signup_btn.clicked.connect(self.handle_register)
        card_layout.addWidget(signup_btn)
        card_layout.addSpacing(14)

        # ---- OR Divider ----
        or_layout = QHBoxLayout()
        or_layout.setSpacing(0)
        left_line = QFrame()
        left_line.setFixedHeight(1)
        left_line.setStyleSheet("background-color: rgba(255, 255, 255, 45);")
        left_line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        or_layout.addWidget(left_line)
        or_text = QLabel("OR")
        or_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        or_text.setFixedWidth(40)
        or_text.setStyleSheet("color: rgba(255,255,255,100); font-size: 10px; background: transparent; font-weight: bold;")
        or_layout.addWidget(or_text)
        right_line = QFrame()
        right_line.setFixedHeight(1)
        right_line.setStyleSheet("background-color: rgba(255, 255, 255, 45);")
        right_line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        or_layout.addWidget(right_line)
        card_layout.addLayout(or_layout)
        card_layout.addSpacing(14)

        # ---- HAVE AN ACCOUNT? LOGIN ----
        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch_layout.setSpacing(5)
        have_label = QLabel("HAVE AN ACCOUNT?")
        have_label.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: bold; background: transparent; letter-spacing: 0.5px;")
        switch_layout.addWidget(have_label)
        login_btn = QPushButton("LOGIN")
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.setStyleSheet("""
            QPushButton { color: #A8D5A2; font-size: 11px; font-weight: bold; background: transparent; border: none; letter-spacing: 0.5px; padding: 0px; }
            QPushButton:hover { color: #C8F0C2; }
        """)
        login_btn.clicked.connect(self.switch_to_login.emit)
        switch_layout.addWidget(login_btn)
        card_layout.addLayout(switch_layout)

        card_layout.addStretch()

        # ---- AMALY Logo ----
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.setSpacing(6)
        logo_icon = QLabel()
        logo_pm = QPixmap(os.path.join(BASE_DIR, "logo.png"))
        if not logo_pm.isNull():
            logo_icon.setPixmap(logo_pm.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo_icon.setText("⌂")
        logo_icon.setStyleSheet("background: transparent;")
        logo_layout.addWidget(logo_icon)
        logo_text = QLabel("AMALY")
        logo_text.setStyleSheet("color: #A8D5A2; font-size: 14px; font-weight: bold; background: transparent; letter-spacing: 3px;")
        logo_layout.addWidget(logo_text)
        card_layout.addLayout(logo_layout)

        main_layout.addWidget(card)

    def _label_style(self):
        return "QLabel { color: rgba(200, 220, 200, 220); font-size: 12px; font-weight: bold; background: transparent; }"

    def _input_style(self):
        return """
            QLineEdit {
                background-color: rgba(255, 255, 255, 15);
                border: 1.5px solid rgba(255, 255, 255, 45);
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 13px;
                color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 1.5px solid rgba(168, 213, 162, 120);
                background-color: rgba(255, 255, 255, 22);
            }
            QLineEdit::placeholder { color: rgba(200, 210, 200, 110); }
        """

    def _combo_style(self):
        return """
            QComboBox {
                background-color: rgba(255, 255, 255, 15);
                border: 1.5px solid rgba(255, 255, 255, 45);
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 13px;
                color: #FFFFFF;
            }
            QComboBox:focus { border: 1.5px solid rgba(168, 213, 162, 120); }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow { image: none; border: none; }
            QComboBox QAbstractItemView {
                background-color: rgba(55, 85, 65, 240);
                color: #FFFFFF;
                selection-background-color: rgba(168, 213, 162, 80);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                padding: 4px;
            }
        """

    # ===================== API LOADING =====================
    def _load_provinsi(self):
        """Load provinsi list from API in background thread."""
        def fetch():
            try:
                r = requests.get("https://equran.id/api/v2/shalat/provinsi", timeout=10)
                data = r.json().get("data", [])
                QMetaObject.invokeMethod(
                    self, "_set_provinsi_list",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(list, data)
                )
            except Exception:
                QMetaObject.invokeMethod(
                    self, "_set_provinsi_list",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(list, [])
                )
        threading.Thread(target=fetch, daemon=True).start()

    from PyQt6.QtCore import pyqtSlot

    @pyqtSlot(list)
    def _set_provinsi_list(self, data):
        self._provinsi_list = data
        self.provinsi_combo.clear()
        if data:
            self.provinsi_combo.addItem("Pilih provinsi...")
            for prov in data:
                self.provinsi_combo.addItem(prov)
        else:
            self.provinsi_combo.addItem("Gagal memuat provinsi")

    def _on_provinsi_changed(self, index):
        """When provinsi selected, load kabkota from API."""
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
                    "https://equran.id/api/v2/shalat/kabkota",
                    json={"provinsi": provinsi},
                    timeout=10
                )
                data = r.json().get("data", [])
                QMetaObject.invokeMethod(
                    self, "_set_kabkota_list",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(list, data)
                )
            except Exception:
                QMetaObject.invokeMethod(
                    self, "_set_kabkota_list",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(list, [])
                )
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
        else:
            self.kabkota_combo.addItem("Gagal memuat data")
            self.kabkota_combo.setEnabled(False)

    def handle_register(self):
        name = self.name_input.text().strip()
        password = self.password_input.text().strip()
        provinsi = self.provinsi_combo.currentText()
        kabkota = self.kabkota_combo.currentText()

        if not name or not password:
            self.show_message("Name and password are required!", False)
            return
        if len(password) < 4:
            self.show_message("Password must be at least 4 characters!", False)
            return
        if self.provinsi_combo.currentIndex() <= 0:
            self.show_message("Pilih provinsi terlebih dahulu!", False)
            return
        if self.kabkota_combo.currentIndex() <= 0:
            self.show_message("Pilih kabupaten/kota terlebih dahulu!", False)
            return

        location = f"{kabkota}, {provinsi}"
        success, msg = self.db.register_user(name, location, password, provinsi, kabkota)
        if success:
            self.show_message("Account created! Please login.", True)
            self.name_input.clear()
            self.provinsi_combo.setCurrentIndex(0)
            self.password_input.clear()
        else:
            self.show_message(msg, False)

    def show_message(self, message, is_success=False):
        self.message_label.setText(message)
        if is_success:
            self.message_label.setStyleSheet("color: #A8D5A2; font-size: 11px; background: transparent;")
        else:
            self.message_label.setStyleSheet("color: #FF6B6B; font-size: 11px; background: transparent;")
        self.message_label.setVisible(True)
