"""
Amalan Harian - Aplikasi Desktop Pencatat Amalan Ibadah Harian
==============================================================

Teknologi:
- Python 3.8+
- PyQt6 (GUI Framework)
- SQLite (Database Lokal)
- requests (HTTP Client untuk API)
- equran.id API (Sumber data Al-Quran)

Fitur Utama:
1. Login & Create Account
2. Input Data Amalan Harian
3. Edit & Hapus Data Amalan
4. Pencarian Data
5. Reminder Ibadah
6. Laporan Perkembangan Amalan
7. Penyimpanan Data ke Database SQLite
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget,
    QWidget, QVBoxLayout
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from database import Database
from ui_login import LoginPage
from ui_register import RegisterPage
from ui_dashboard import DashboardPage
from ui_sholat import SholatPage
from ui_quran import QuranPage
from ui_sedekahTracker import SedekahTrackerPage
from ui_settings import SettingsPage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── DEV: set True to bypass login and go straight to dashboard ──
SKIP_LOGIN = False
# ────────────────────────────────────────────────────────────────


class MainWindow(QMainWindow):
    """Window utama aplikasi Amalan Harian"""

    def __init__(self):
        super().__init__()

        # Inisialisasi database
        self.db = Database()

        # Data user yang sedang login
        self.current_user = None

        # Setup window
        self.setWindowTitle("Amalan Harian - Pencatat Ibadah Harian")
        self.setMinimumSize(1100, 700)
        self.setFixedSize(1100, 700)

        # Center window on screen
        self.center_window()

        # Stacked widget untuk navigasi antar halaman
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Setup halaman-halaman
        self.setup_pages()

        # Tampilkan halaman login (atau langsung dashboard jika SKIP_LOGIN)
        if SKIP_LOGIN:
            self.current_user = {"nama_lengkap": "Dev User", "location": "Jakarta"}
            self.show_dashboard()
        else:
            self.show_login()

        # Apply global stylesheet
        self.setStyleSheet(self._global_style())

    def center_window(self):
        """Menempatkan window di tengah layar"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def setup_pages(self):
        """Inisialisasi semua halaman"""
        # Login Page
        self.login_page = LoginPage(self.db)
        self.login_page.switch_to_register.connect(self.show_register)
        self.login_page.login_success.connect(self.on_login_success)

        # Register Page
        self.register_page = RegisterPage(self.db)
        self.register_page.switch_to_login.connect(self.show_login)
        self.register_page.register_success.connect(self.on_register_success)

        # Dashboard Page
        self.dashboard_page = DashboardPage(self.db)
        self.dashboard_page.logout_signal.connect(self.on_logout)
        self.dashboard_page.navigate_sholat.connect(self.show_sholat)
        self.dashboard_page.navigate_quran.connect(self.show_quran)
        self.dashboard_page.navigate_sedekah.connect(self.show_sedekah)
        self.dashboard_page.navigate_settings.connect(self.show_settings)

        # Sholat Page
        self.sholat_page = SholatPage(self.db)
        self.sholat_page.back_to_dashboard.connect(self.show_dashboard)

        # Quran Page
        self.quran_page = QuranPage(self.db)
        self.quran_page.back_to_dashboard.connect(self.show_dashboard)

        # Sedekah Tracker Page
        self.sedekah_page = SedekahTrackerPage(self.db)
        self.sedekah_page.back_to_dashboard.connect(self.show_dashboard)

        # Settings Page
        self.settings_page = SettingsPage(self.db)
        self.settings_page.back_to_dashboard.connect(self.show_dashboard)
        self.settings_page.logout_signal.connect(self.on_logout)
        self.settings_page.arab_size_changed.connect(self._on_arab_size_changed)

        # Tambahkan ke stacked widget
        self.stacked_widget.addWidget(self.login_page)      # index 0
        self.stacked_widget.addWidget(self.register_page)    # index 1
        self.stacked_widget.addWidget(self.dashboard_page)   # index 2
        self.stacked_widget.addWidget(self.sholat_page)      # index 3
        self.stacked_widget.addWidget(self.quran_page)       # index 4
        self.stacked_widget.addWidget(self.sedekah_page)     # index 5
        self.stacked_widget.addWidget(self.settings_page)     # index 6

    def show_login(self):
        """Menampilkan halaman login"""
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.setWindowTitle("Amalan Harian - Masuk")

    def show_register(self):
        """Menampilkan halaman registrasi"""
        self.stacked_widget.setCurrentWidget(self.register_page)
        self.setWindowTitle("Amalan Harian - Buat Akun")

    def show_dashboard(self):
        """Menampilkan halaman dasbor"""
        self.dashboard_page.set_user_data(self.current_user)
        self.stacked_widget.setCurrentWidget(self.dashboard_page)
        self.setWindowTitle("AMALY - Dashboard")

    def show_sholat(self):
        """Menampilkan halaman jadwal sholat"""
        self.sholat_page.set_user_data(self.current_user)
        self.stacked_widget.setCurrentWidget(self.sholat_page)
        self.setWindowTitle("AMALY - Jadwal Sholat")

    def show_quran(self):
        """Menampilkan halaman Al-Qur'an"""
        self.quran_page.set_user_data(self.current_user)
        self.stacked_widget.setCurrentWidget(self.quran_page)
        self.setWindowTitle("AMALY - Al-Qur'an")

    def show_sedekah(self):
        """Menampilkan halaman Sedekah Tracker"""
        self.sedekah_page.set_user_data(self.current_user)
        self.stacked_widget.setCurrentWidget(self.sedekah_page)
        self.setWindowTitle("AMALY - Sedekah Tracker")

    def show_settings(self):
        """Menampilkan halaman Settings"""
        self.settings_page.set_user_data(self.current_user)
        self.stacked_widget.setCurrentWidget(self.settings_page)
        self.setWindowTitle("AMALY - Settings")

    def _on_arab_size_changed(self, size):
        """Propagate arab text size change to Quran page"""
        self.quran_page.set_arab_font_size(size)

    def on_login_success(self, user_data):
        """Handler ketika login berhasil"""
        self.current_user = user_data
        self.show_dashboard()

    def on_register_success(self):
        """Handler ketika registrasi berhasil"""
        # Otomatis pindah ke halaman login setelah 1.5 detik
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, self.show_login)

    def on_logout(self):
        """Handler ketika user logout"""
        self.current_user = None
        self.show_login()

    def _global_style(self):
        """Stylesheet global untuk seluruh aplikasi"""
        return """
            * {
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QMainWindow {
                background-color: #F0F4F0;
            }
        """

    def closeEvent(self, event):
        """Handler ketika window ditutup"""
        self.db.close()
        event.accept()


def main():
    """Entry point aplikasi"""
    # Mengaktifkan high DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("Amalan Harian")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SMK DPK")

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
