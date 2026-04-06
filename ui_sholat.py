"""
Sholat Page - AMALY
Full prayer schedule, fardhu checklist with database persistence,
and weekly progress bar.
"""

import os
import threading
import requests
from datetime import datetime, date

from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QProgressBar, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
    QPushButton,
)

from ui_dashboard import IconWidget, BannerWidget

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class SholatPage(QWidget):
    """Halaman Jadwal Sholat — jadwal lengkap + checklist fardhu + progress."""

    back_to_dashboard = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_data = None
        self.user_id = None
        self.user_provinsi = ""
        self.user_kabkota = ""
        self._prayer_data = {}  # jadwal hari ini dari API
        self._checklist_widgets = {}
        self.setup_ui()

    def set_user_data(self, data):
        if not data:
            return
        self.user_data = data
        self.user_id = data.get("id")
        self.user_provinsi = data.get("provinsi", "")
        self.user_kabkota = data.get("kabkota", "")
        loc = data.get("location", "Indonesia") or "Indonesia"
        self.loc_label.setText(f"{loc}")
        self._load_prayer_times()
        self._refresh_checklist()

    # ─────────────── LAYOUT ───────────────
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
            logo_img.setPixmap(logo_pixmap.scaled(
                44, 44,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        logo_img.setStyleSheet("background:transparent;")
        logo_row.addWidget(logo_img)

        logo_text = QLabel("AMALY")
        logo_text.setStyleSheet(
            "color:#FFF;font-size:20px;font-weight:bold;"
            "background:transparent;letter-spacing:4px;"
        )
        logo_row.addWidget(logo_text)
        lay.addLayout(logo_row)
        lay.addSpacing(42)

        menu_items = [
            ("home", "Dashboard", False),
            ("mosque", "Jadwal Sholat", True),
            ("book", "Al-Qur'an", False),
            ("chart", "Sedekah Tracker", False),
        ]
        self._sidebar_btns = {}
        for ic_name, label, active in menu_items:
            btn = self._sidebar_btn(ic_name, label, active)
            self._sidebar_btns[label] = btn
            lay.addWidget(btn)
            lay.addSpacing(4)

        # Dashboard click -> back signal
        self._sidebar_btns["Dashboard"].mousePressEvent = lambda e: self.back_to_dashboard.emit()

        lay.addStretch()

        settings_btn = self._sidebar_btn("gear", "Settings", False)
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
        ic = IconWidget(icon_name, 20, ic_color)
        h.addWidget(ic)
        lbl = QLabel(text)
        fw = "bold" if active else "normal"
        c = "#FFF" if active else "rgba(255,255,255,140)"
        lbl.setStyleSheet(f"color:{c};font-size:14px;font-weight:{fw};background:transparent;")
        h.addWidget(lbl)
        h.addStretch()
        bg = "rgba(255,255,255,15)" if active else "transparent"
        btn.setStyleSheet(f"background:{bg};border-radius:12px;")
        return btn

    # ─────────────── CONTENT AREA ───────────────
    def _build_content(self):
        wrapper = QWidget()
        wrapper.setStyleSheet("background-color:#ECEEE7;")
        col = QVBoxLayout(wrapper)
        col.setContentsMargins(28, 20, 28, 12)
        col.setSpacing(0)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Jadwal Sholat")
        title.setStyleSheet("font-size:24px;font-weight:bold;color:#1A3C2A;background:transparent;")
        title_row.addWidget(title)
        title_row.addStretch()
        self.loc_label = QLabel("Indonesia")
        self.loc_label.setStyleSheet("font-size:13px;color:#666;background:transparent;")
        title_row.addWidget(IconWidget("location", 16, QColor("#666")))
        title_row.addWidget(self.loc_label)
        col.addLayout(title_row)
        col.addSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        vb = QVBoxLayout(inner)
        vb.setContentsMargins(0, 0, 6, 0)
        vb.setSpacing(18)

        # 1) Full schedule card
        vb.addWidget(self._build_schedule_card())

        # 2) Checklist fardhu card
        vb.addWidget(self._build_checklist_card())

        # 3) Progress card
        vb.addWidget(self._build_progress_card())

        vb.addStretch()
        scroll.setWidget(inner)
        col.addWidget(scroll)
        return wrapper

    # ═══════════════════════════════════════════
    #  1. JADWAL SHOLAT LENGKAP
    # ═══════════════════════════════════════════
    def _build_schedule_card(self):
        card = QFrame()
        card.setObjectName("scheduleCard")
        card.setStyleSheet("""
            QFrame#scheduleCard {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #1A3C2A, stop:1 #2D6B4A);
                border-radius: 18px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)

        v = QVBoxLayout(card)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(6)

        header = QHBoxLayout()
        h_title = QLabel("Jadwal Sholat Hari Ini")
        h_title.setStyleSheet("color:#FFF;font-size:18px;font-weight:bold;background:transparent;")
        header.addWidget(h_title)
        header.addStretch()
        self.date_label = QLabel(datetime.now().strftime("%A, %d %B %Y"))
        self.date_label.setStyleSheet("color:rgba(255,255,255,160);font-size:12px;background:transparent;")
        header.addWidget(self.date_label)
        v.addLayout(header)
        v.addSpacing(12)

        # Grid of prayer times (8 items: imsak, subuh, terbit, dhuha, dzuhur, ashar, maghrib, isya)
        self._schedule_labels = {}
        schedule_items = [
            ("Imsak", "imsak", "#FFD88E"),
            ("Subuh", "subuh", "#FFFFFF"),
            ("Terbit", "terbit", "#FFD88E"),
            ("Dhuha", "dhuha", "#FFD88E"),
            ("Dzuhur", "dzuhur", "#FFFFFF"),
            ("Ashar", "ashar", "#FFFFFF"),
            ("Maghrib", "maghrib", "#FFFFFF"),
            ("Isya", "isya", "#FFFFFF"),
        ]

        # Row 1: 4 items
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        for name, key, color in schedule_items[:4]:
            w, lbl = self._schedule_time_widget(name, "--:--", color)
            self._schedule_labels[key] = lbl
            row1.addWidget(w)
        v.addLayout(row1)
        v.addSpacing(8)

        # Row 2: 4 items
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        for name, key, color in schedule_items[4:]:
            w, lbl = self._schedule_time_widget(name, "--:--", color)
            self._schedule_labels[key] = lbl
            row2.addWidget(w)
        v.addLayout(row2)

        return card

    def _schedule_time_widget(self, name, time_str, accent_color):
        """Single prayer time box inside the schedule card."""
        frame = QFrame()
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        frame.setFixedHeight(72)
        frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,10);
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,12);
            }
        """)
        v = QVBoxLayout(frame)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(4)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        nm = QLabel(name)
        nm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nm.setStyleSheet("font-size:11px;color:rgba(255,255,255,160);background:transparent;")
        v.addWidget(nm)

        tm = QLabel(time_str)
        tm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tm.setStyleSheet(f"font-size:18px;font-weight:bold;color:{accent_color};background:transparent;")
        v.addWidget(tm)

        return frame, tm

    # ═══════════════════════════════════════════
    #  2. CHECKLIST SHOLAT FARDHU
    # ═══════════════════════════════════════════
    def _build_checklist_card(self):
        card = QFrame()
        card.setObjectName("checklistCard")
        card.setStyleSheet("""
            QFrame#checklistCard {
                background: #FFFFFF;
                border-radius: 18px;
                border: 1px solid rgba(0,0,0,6);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        v = QVBoxLayout(card)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(14)

        header = QHBoxLayout()
        h_title = QLabel("Checklist Sholat Fardhu Hari Ini")
        h_title.setStyleSheet("font-size:16px;font-weight:bold;color:#1A3C2A;background:transparent;")
        header.addWidget(h_title)
        header.addStretch()
        self.checklist_pct_label = QLabel("0%")
        self.checklist_pct_label.setStyleSheet("font-size:14px;font-weight:bold;color:#2D6B4A;background:transparent;")
        header.addWidget(self.checklist_pct_label)
        v.addLayout(header)

        # Progress bar for today
        self.checklist_bar = QProgressBar()
        self.checklist_bar.setValue(0)
        self.checklist_bar.setTextVisible(False)
        self.checklist_bar.setFixedHeight(10)
        self.checklist_bar.setStyleSheet("""
            QProgressBar {background:#E4E8DE;border:none;border-radius:5px;}
            QProgressBar::chunk {background:#2D6B4A;border-radius:5px;}
        """)
        v.addWidget(self.checklist_bar)
        v.addSpacing(4)

        # 5 fardhu prayer checkboxes
        prayers = [
            ("subuh", "Subuh", "sunrise"),
            ("dzuhur", "Dzuhur", "sun"),
            ("ashar", "Ashar", "cloud_sun"),
            ("maghrib", "Maghrib", "sunset"),
            ("isya", "Isya", "moon"),
        ]
        for key, name, icon_name in prayers:
            row = self._checklist_row(key, name, icon_name)
            v.addWidget(row)

        return card

    def _checklist_row(self, key, name, icon_name):
        """Single checklist row for a fardhu prayer."""
        row = QFrame()
        row.setFixedHeight(52)
        row.setStyleSheet("""
            QFrame {
                background: #F8FAF6;
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,5);
            }
            QFrame:hover { background: #EFF3EB; }
        """)
        row.setCursor(Qt.CursorShape.PointingHandCursor)

        h = QHBoxLayout(row)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(14)

        ic = IconWidget(icon_name, 22, QColor("#2D6B4A"))
        h.addWidget(ic)

        lbl = QLabel(name)
        lbl.setStyleSheet("font-size:14px;color:#333;font-weight:600;background:transparent;")
        h.addWidget(lbl)
        h.addStretch()

        # Time label (will be filled from schedule)
        time_lbl = QLabel("--:--")
        time_lbl.setStyleSheet("font-size:12px;color:#999;background:transparent;")
        h.addWidget(time_lbl)

        # Check indicator
        check_lbl = QLabel("○")
        check_lbl.setFixedSize(28, 28)
        check_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check_lbl.setStyleSheet("""
            QLabel {
                font-size:18px;
                color: #CCC;
                background: transparent;
            }
        """)
        h.addWidget(check_lbl)

        self._checklist_widgets[key] = {
            "row": row,
            "check": check_lbl,
            "time": time_lbl,
            "checked": False,
        }

        row.mousePressEvent = lambda e, k=key: self._on_toggle_sholat(k)

        return row

    def _on_toggle_sholat(self, key):
        """Toggle sholat in DB and update UI."""
        if not self.user_id:
            return
        new_val = self.db.toggle_sholat(self.user_id, key)
        self._checklist_widgets[key]["checked"] = bool(new_val)
        self._update_check_ui(key, bool(new_val))
        self._update_checklist_progress()

    def _update_check_ui(self, key, checked):
        w = self._checklist_widgets[key]
        if checked:
            w["check"].setText("✓")
            w["check"].setStyleSheet("""
                QLabel {
                    font-size:16px; font-weight:bold;
                    color: #FFF; background: #2D6B4A;
                    border-radius: 14px;
                }
            """)
            w["row"].setStyleSheet("""
                QFrame {
                    background: #EAF5E6;
                    border-radius: 12px;
                    border: 1px solid rgba(45,107,74,20);
                }
            """)
        else:
            w["check"].setText("○")
            w["check"].setStyleSheet("""
                QLabel {
                    font-size:18px; color: #CCC;
                    background: transparent;
                }
            """)
            w["row"].setStyleSheet("""
                QFrame {
                    background: #F8FAF6;
                    border-radius: 12px;
                    border: 1px solid rgba(0,0,0,5);
                }
                QFrame:hover { background: #EFF3EB; }
            """)

    def _update_checklist_progress(self):
        done = sum(1 for w in self._checklist_widgets.values() if w["checked"])
        pct = int(done / 5 * 100)
        self.checklist_bar.setValue(pct)
        self.checklist_pct_label.setText(f"{pct}%")

    def _refresh_checklist(self):
        """Load checklist from DB and update UI."""
        if not self.user_id:
            return
        data = self.db.get_sholat_today(self.user_id)
        for key in ("subuh", "dzuhur", "ashar", "maghrib", "isya"):
            checked = bool(data.get(key, 0))
            self._checklist_widgets[key]["checked"] = checked
            self._update_check_ui(key, checked)
        self._update_checklist_progress()
        self._refresh_weekly_progress()

    # ═══════════════════════════════════════════
    #  3. PROGRESS MINGGUAN
    # ═══════════════════════════════════════════
    def _build_progress_card(self):
        card = QFrame()
        card.setObjectName("progressWeeklyCard")
        card.setStyleSheet("""
            QFrame#progressWeeklyCard {
                background: #FFFFFF;
                border-radius: 18px;
                border: 1px solid rgba(0,0,0,6);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        v = QVBoxLayout(card)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(14)

        h_title = QLabel("Progress Sholat Fardhu (7 Hari Terakhir)")
        h_title.setStyleSheet("font-size:16px;font-weight:bold;color:#1A3C2A;background:transparent;")
        v.addWidget(h_title)

        # Overall progress
        overall_h = QHBoxLayout()
        self.overall_pct_label = QLabel("0%")
        self.overall_pct_label.setStyleSheet("font-size:28px;font-weight:bold;color:#2D6B4A;background:transparent;")
        overall_h.addWidget(self.overall_pct_label)
        overall_h.addSpacing(12)
        overall_sub = QLabel("capaian minggu ini")
        overall_sub.setStyleSheet("font-size:12px;color:#999;background:transparent;")
        overall_h.addWidget(overall_sub)
        overall_h.addStretch()
        v.addLayout(overall_h)

        self.overall_bar = QProgressBar()
        self.overall_bar.setValue(0)
        self.overall_bar.setTextVisible(False)
        self.overall_bar.setFixedHeight(14)
        self.overall_bar.setStyleSheet("""
            QProgressBar {background:#E4E8DE;border:none;border-radius:7px;}
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1A3C2A, stop:1 #4AA06C);
                border-radius:7px;
            }
        """)
        v.addWidget(self.overall_bar)
        v.addSpacing(10)

        # Per-prayer weekly bars
        self._weekly_bars = {}
        for key, name, color in [
            ("subuh", "Subuh", "#2D6B4A"),
            ("dzuhur", "Dzuhur", "#3A8D5E"),
            ("ashar", "Ashar", "#4AA06C"),
            ("maghrib", "Maghrib", "#5BB87E"),
            ("isya", "Isya", "#6BCF90"),
        ]:
            bar_w, bar, pct_lbl = self._weekly_bar_row(name, color)
            self._weekly_bars[key] = (bar, pct_lbl)
            v.addWidget(bar_w)

        return card

    def _weekly_bar_row(self, name, color):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        top = QHBoxLayout()
        nm = QLabel(name)
        nm.setStyleSheet("font-size:12px;color:#555;font-weight:600;background:transparent;")
        top.addWidget(nm)
        top.addStretch()
        pct_lbl = QLabel("0/7")
        pct_lbl.setStyleSheet("font-size:11px;color:#999;background:transparent;")
        top.addWidget(pct_lbl)
        v.addLayout(top)
        bar = QProgressBar()
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        bar.setStyleSheet(f"""
            QProgressBar {{background:#E4E8DE;border:none;border-radius:4px;}}
            QProgressBar::chunk {{background:{color};border-radius:4px;}}
        """)
        v.addWidget(bar)
        return w, bar, pct_lbl

    def _refresh_weekly_progress(self):
        """Calculate and display weekly sholat progress."""
        if not self.user_id:
            return
        weekly = self.db.get_sholat_weekly(self.user_id)
        totals = {"subuh": 0, "dzuhur": 0, "ashar": 0, "maghrib": 0, "isya": 0}
        for row in weekly:
            for k in totals:
                totals[k] += row.get(k, 0)

        grand_total = sum(totals.values())
        max_total = 7 * 5  # 7 days * 5 prayers
        overall_pct = int(grand_total / max_total * 100) if max_total else 0
        self.overall_pct_label.setText(f"{overall_pct}%")
        self.overall_bar.setValue(overall_pct)

        for key, (bar, pct_lbl) in self._weekly_bars.items():
            count = totals[key]
            pct_lbl.setText(f"{count}/7")
            bar.setValue(int(count / 7 * 100))

    # ─────────────── PRAYER TIMES API ───────────────
    def _load_prayer_times(self):
        provinsi = self.user_provinsi
        kabkota = self.user_kabkota
        if not provinsi or not kabkota:
            return
        now = datetime.now()

        def fetch():
            try:
                r = requests.post(
                    "https://equran.id/api/v2/shalat",
                    json={
                        "provinsi": provinsi,
                        "kabkota": kabkota,
                        "bulan": now.month,
                        "tahun": now.year,
                    },
                    timeout=15,
                )
                resp = r.json()
                jadwal_list = resp.get("data", {}).get("jadwal", [])
                today_str = now.strftime("%Y-%m-%d")
                today_jadwal = {}
                for j in jadwal_list:
                    if j.get("tanggal_lengkap") == today_str or j.get("tanggal") == now.day:
                        today_jadwal = j
                        break
                QMetaObject.invokeMethod(
                    self, "_apply_prayer_times",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(dict, today_jadwal),
                )
            except Exception:
                pass

        threading.Thread(target=fetch, daemon=True).start()

    @pyqtSlot(dict)
    def _apply_prayer_times(self, jadwal):
        self._prayer_data = jadwal

        # Update schedule card labels
        for key in ("imsak", "subuh", "terbit", "dhuha", "dzuhur", "ashar", "maghrib", "isya"):
            if key in self._schedule_labels:
                self._schedule_labels[key].setText(jadwal.get(key, "--:--"))

        # Update date
        hari = jadwal.get("hari", "")
        tgl = jadwal.get("tanggal_lengkap", "")
        if hari and tgl:
            self.date_label.setText(f"{hari}, {tgl}")

        # Update checklist time labels
        for key in ("subuh", "dzuhur", "ashar", "maghrib", "isya"):
            if key in self._checklist_widgets:
                self._checklist_widgets[key]["time"].setText(jadwal.get(key, "--:--"))
