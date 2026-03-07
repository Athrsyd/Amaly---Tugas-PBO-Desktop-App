"""
Login Page - AMALY - Glassmorphism Design
Matches: WELCOME BACK! centered card with full background image
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QPainter, QLinearGradient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class LoginPage(QWidget):
    """Halaman Login - Glassmorphism centered card"""

    switch_to_register = pyqtSignal()
    login_success = pyqtSignal(dict)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.bg_pixmap = None
        self._load_background()
        self.setup_ui()

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
        card.setFixedSize(400, 490)
        card.setObjectName("glassCard")
        card.setStyleSheet("""
            QFrame#glassCard {
                background-color: rgba(55, 85, 65, 160);
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 28);
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(45, 40, 45, 25)
        card_layout.setSpacing(0)

        # ---- Title: WELCOME BACK! ----
        title = QLabel("WELCOME BACK!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: bold;
                font-style: italic;
                background: transparent;
                letter-spacing: 1px;
            }
        """)
        card_layout.addWidget(title)
        card_layout.addSpacing(5)

        # ---- Subtitle ----
        subtitle = QLabel("Continue your journey with Amaly")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(200, 220, 200, 200);
                font-size: 12px;
                background: transparent;
            }
        """)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(32)

        # ---- Name Field ----
        name_label = QLabel("Name")
        name_label.setStyleSheet(self._label_style())
        card_layout.addWidget(name_label)
        card_layout.addSpacing(6)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")
        self.name_input.setMinimumHeight(46)
        self.name_input.setStyleSheet(self._input_style())
        card_layout.addWidget(self.name_input)
        card_layout.addSpacing(18)

        # ---- Password Field ----
        pw_label = QLabel("Password")
        pw_label.setStyleSheet(self._label_style())
        card_layout.addWidget(pw_label)
        card_layout.addSpacing(6)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(46)
        self.password_input.setStyleSheet(self._input_style())
        self.password_input.returnPressed.connect(self.handle_login)
        card_layout.addWidget(self.password_input)
        card_layout.addSpacing(6)

        # ---- Error Label ----
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: #FF6B6B; font-size: 11px; background: transparent;")
        self.error_label.setVisible(False)
        self.error_label.setFixedHeight(18)
        card_layout.addWidget(self.error_label)
        card_layout.addSpacing(10)

        # ---- LOGIN Button ----
        login_btn = QPushButton("LOGIN")
        login_btn.setMinimumHeight(50)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #1B4332;
                color: #FFFFFF;
                border: none;
                border-radius: 75px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 3px;
            }
            QPushButton:hover { background-color: #245639; }
            QPushButton:pressed { background-color: #143326; }
        """)
        login_btn.clicked.connect(self.handle_login)
        card_layout.addWidget(login_btn)
        card_layout.addSpacing(16)

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
        card_layout.addSpacing(16)

        # ---- HAVE NOT AN ACCOUNT? SIGN UP ----
        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        switch_layout.setSpacing(5)
        have_label = QLabel("HAVE NOT AN ACCOUNT?")
        have_label.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: bold; background: transparent; letter-spacing: 0.5px;")
        switch_layout.addWidget(have_label)
        signup_btn = QPushButton("SIGN UP")
        signup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        signup_btn.setStyleSheet("""
            QPushButton { color: #A8D5A2; font-size: 11px; font-weight: bold; background: transparent; border: none; letter-spacing: 0.5px; padding: 0px; }
            QPushButton:hover { color: #C8F0C2; }
        """)
        signup_btn.clicked.connect(self.switch_to_register.emit)
        switch_layout.addWidget(signup_btn)
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

    def handle_login(self):
        name = self.name_input.text().strip()
        password = self.password_input.text().strip()
        if not name or not password:
            self.show_error("Please fill in all fields!")
            return
        success, result = self.db.login_user(name, password)
        if success:
            self.error_label.setVisible(False)
            self.name_input.clear()
            self.password_input.clear()
            self.login_success.emit(result)
        else:
            self.show_error("Invalid name or password!")

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.setVisible(True)
