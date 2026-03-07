"""
Dashboard Page - AMALY
Sidebar + Main Content with Banner (incl. Prayer Times), Daily Activity, Info Cards
Uses QPainter vector icons (no emojis). Logo from 'image 4 (2).svg'.
"""

import math
import os
import threading
import requests
from datetime import datetime, date

from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import (
    QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
)
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QLineEdit,
    QProgressBar, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════
#  ICON WIDGET — QPainter vector icons (safe, no path subtraction)
# ══════════════════════════════════════════════════════════════════

class IconWidget(QWidget):
    """Draws a named vector icon using QPainter."""

    def __init__(self, name: str, size: int = 24, color: QColor = None, parent=None):
        super().__init__(parent)
        self._name = name
        self._size = size
        self._color = color or QColor(255, 255, 255)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self._color
        s = self._size
        m = s * 0.12
        draw_fn = getattr(self, f"_draw_{self._name}", self._draw_fallback)
        draw_fn(p, m, s - m, c)
        p.end()

    # ─── Sidebar icons ───

    def _draw_home(self, p, lo, hi, c):
        mid = (lo + hi) / 2
        w = hi - lo
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        roof = QPainterPath()
        roof.moveTo(mid, lo)
        roof.lineTo(hi, lo + w * 0.45)
        roof.lineTo(lo, lo + w * 0.45)
        roof.closeSubpath()
        p.drawPath(roof)
        p.drawRoundedRect(QRectF(lo + w * 0.18, lo + w * 0.40, w * 0.64, w * 0.52), 2, 2)
        p.setBrush(QColor(26, 60, 42))
        p.drawRoundedRect(QRectF(mid - w * 0.10, lo + w * 0.58, w * 0.20, w * 0.34), 2, 2)

    def _draw_mosque(self, p, lo, hi, c):
        mid = (lo + hi) / 2
        w = hi - lo
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        dome = QPainterPath()
        dome.moveTo(lo + w * 0.2, lo + w * 0.55)
        dome.quadTo(mid, lo + w * 0.05, hi - w * 0.2, lo + w * 0.55)
        dome.closeSubpath()
        p.drawPath(dome)
        p.drawRect(QRectF(lo + w * 0.15, lo + w * 0.50, w * 0.70, w * 0.40))
        mw = w * 0.08
        p.drawRect(QRectF(lo, lo + w * 0.30, mw, w * 0.60))
        p.drawRect(QRectF(hi - mw, lo + w * 0.30, mw, w * 0.60))
        # crescent dot on top
        p.drawEllipse(QPointF(mid, lo + w * 0.08), w * 0.04, w * 0.04)

    def _draw_book(self, p, lo, hi, c):
        w = hi - lo
        mid = (lo + hi) / 2
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(c, 1.8))
        lp = QPainterPath()
        lp.moveTo(mid, lo + w * 0.12)
        lp.quadTo(lo + w * 0.15, lo + w * 0.12, lo, lo + w * 0.22)
        lp.lineTo(lo, hi - w * 0.08)
        lp.quadTo(lo + w * 0.15, hi - w * 0.15, mid, hi - w * 0.08)
        p.drawPath(lp)
        rp = QPainterPath()
        rp.moveTo(mid, lo + w * 0.12)
        rp.quadTo(hi - w * 0.15, lo + w * 0.12, hi, lo + w * 0.22)
        rp.lineTo(hi, hi - w * 0.08)
        rp.quadTo(hi - w * 0.15, hi - w * 0.15, mid, hi - w * 0.08)
        p.drawPath(rp)
        p.drawLine(QPointF(mid, lo + w * 0.12), QPointF(mid, hi - w * 0.08))

    def _draw_chart(self, p, lo, hi, c):
        w = hi - lo
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        bw = w * 0.18
        gap = w * 0.06
        x = lo + w * 0.08
        for frac in [0.55, 0.80, 0.40, 1.0]:
            bh = (w * 0.75) * frac
            p.drawRoundedRect(QRectF(x, hi - w * 0.05 - bh, bw, bh), 3, 3)
            x += bw + gap

    def _draw_gear(self, p, lo, hi, c):
        mid = (lo + hi) / 2
        r_out = (hi - lo) * 0.42
        r_in = r_out * 0.68
        teeth = 8
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        path = QPainterPath()
        for i in range(teeth):
            a1 = math.radians(i * 360 / teeth - 11)
            a2 = math.radians(i * 360 / teeth + 11)
            a3 = math.radians(i * 360 / teeth + 360 / teeth / 2 - 7)
            a4 = math.radians(i * 360 / teeth + 360 / teeth / 2 + 7)
            pt = QPointF(mid + r_out * math.cos(a1), mid + r_out * math.sin(a1))
            if i == 0:
                path.moveTo(pt)
            else:
                path.lineTo(pt)
            path.lineTo(QPointF(mid + r_out * math.cos(a2), mid + r_out * math.sin(a2)))
            path.lineTo(QPointF(mid + r_in * math.cos(a3), mid + r_in * math.sin(a3)))
            path.lineTo(QPointF(mid + r_in * math.cos(a4), mid + r_in * math.sin(a4)))
        path.closeSubpath()
        p.drawPath(path)
        # center circle (draw with background color to simulate hole)
        p.setBrush(QColor(26, 60, 42))
        p.drawEllipse(QPointF(mid, mid), r_out * 0.28, r_out * 0.28)

    # ─── Prayer icons ───

    def _draw_sunrise(self, p, lo, hi, c):
        mid = (lo + hi) / 2
        w = hi - lo
        hy = lo + w * 0.62
        sr = w * 0.20
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        arc = QPainterPath()
        arc.moveTo(mid - sr, hy)
        arc.arcTo(QRectF(mid - sr, hy - sr, sr * 2, sr * 2), 180, -180)
        arc.closeSubpath()
        p.drawPath(arc)
        p.setPen(QPen(c, 1.6))
        for a in [0, 30, 60, 90, 120, 150, 180]:
            rad = math.radians(a)
            r1 = sr + w * 0.06
            r2 = sr + w * 0.14
            p.drawLine(QPointF(mid + r1 * math.cos(rad), hy - r1 * math.sin(rad)),
                       QPointF(mid + r2 * math.cos(rad), hy - r2 * math.sin(rad)))
        p.setPen(QPen(c, 2.0))
        p.drawLine(QPointF(lo, hy), QPointF(hi, hy))

    def _draw_sun(self, p, lo, hi, c):
        mid = (lo + hi) / 2
        w = hi - lo
        sr = w * 0.18
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        p.drawEllipse(QPointF(mid, mid), sr, sr)
        p.setPen(QPen(c, 1.8))
        for i in range(8):
            a = math.radians(i * 45)
            r1 = sr + w * 0.06
            r2 = sr + w * 0.16
            p.drawLine(QPointF(mid + r1 * math.cos(a), mid + r1 * math.sin(a)),
                       QPointF(mid + r2 * math.cos(a), mid + r2 * math.sin(a)))

    def _draw_cloud_sun(self, p, lo, hi, c):
        w = hi - lo
        sx, sy, sr = lo + w * 0.68, lo + w * 0.25, w * 0.13
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        p.drawEllipse(QPointF(sx, sy), sr, sr)
        p.setPen(QPen(c, 1.4))
        for i in range(6):
            a = math.radians(i * 60)
            p.drawLine(QPointF(sx + (sr + w * 0.04) * math.cos(a), sy + (sr + w * 0.04) * math.sin(a)),
                       QPointF(sx + (sr + w * 0.09) * math.cos(a), sy + (sr + w * 0.09) * math.sin(a)))
        p.setPen(Qt.PenStyle.NoPen)
        cy = lo + w * 0.58
        cloud = QPainterPath()
        cloud.addEllipse(QPointF(lo + w * 0.30, cy), w * 0.15, w * 0.12)
        cloud.addEllipse(QPointF(lo + w * 0.48, cy - w * 0.06), w * 0.17, w * 0.15)
        cloud.addEllipse(QPointF(lo + w * 0.64, cy), w * 0.13, w * 0.11)
        cloud.addRect(QRectF(lo + w * 0.17, cy, w * 0.60, w * 0.16))
        p.drawPath(cloud)

    def _draw_sunset(self, p, lo, hi, c):
        mid = (lo + hi) / 2
        w = hi - lo
        hy = lo + w * 0.55
        sr = w * 0.16
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        # half sun using clip rect (safe, no path subtraction)
        p.save()
        p.setClipRect(QRectF(lo, lo, w, hy - lo))
        p.drawEllipse(QPointF(mid, hy), sr, sr)
        p.restore()
        p.setPen(QPen(c, 1.5))
        for a in [20, 50, 80, 100, 130, 160]:
            rad = math.radians(a)
            r1, r2 = sr + w * 0.05, sr + w * 0.13
            p.drawLine(QPointF(mid + r1 * math.cos(rad), hy - r1 * math.sin(rad)),
                       QPointF(mid + r2 * math.cos(rad), hy - r2 * math.sin(rad)))
        p.setPen(QPen(c, 2.0))
        p.drawLine(QPointF(lo, hy), QPointF(hi, hy))
        # silhouette
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        bh = w * 0.16
        p.drawRect(QRectF(lo + w * 0.05, hi - bh, w * 0.11, bh))
        p.drawRect(QRectF(lo + w * 0.20, hi - bh * 1.2, w * 0.07, bh * 1.2))
        p.drawRect(QRectF(hi - w * 0.20, hi - bh * 0.9, w * 0.09, bh * 0.9))

    def _draw_moon(self, p, lo, hi, c):
        """Crescent moon using clip instead of path subtraction (safe)."""
        mid = (lo + hi) / 2
        w = hi - lo
        r = w * 0.34
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        # Draw full circle
        p.drawEllipse(QPointF(mid, mid), r, r)
        # Cut with background-colored circle to make crescent
        bg = QColor(0, 0, 0, 0)  # transparent won't work here, use save/clip
        p.save()
        # Use erase composition to cut the hole
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        p.drawEllipse(QPointF(mid + r * 0.50, mid - r * 0.18), r * 0.78, r * 0.78)
        p.restore()
        # stars
        p.setBrush(c)
        p.drawEllipse(QPointF(lo + w * 0.22, lo + w * 0.25), 1.5, 1.5)
        p.drawEllipse(QPointF(lo + w * 0.15, lo + w * 0.52), 1.2, 1.2)

    def _draw_crescent(self, p, lo, hi, c):
        """Simple crescent for banner — uses clip, no path ops."""
        mid = (lo + hi) / 2
        w = hi - lo
        r = w * 0.36
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        p.drawEllipse(QPointF(mid, mid), r, r)
        p.save()
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        p.drawEllipse(QPointF(mid + r * 0.50, mid - r * 0.20), r * 0.78, r * 0.78)
        p.restore()

    # ─── Top bar icons ───

    def _draw_bell(self, p, lo, hi, c):
        mid = (lo + hi) / 2
        w = hi - lo
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        bell = QPainterPath()
        bell.moveTo(mid, lo + w * 0.10)
        bell.quadTo(lo + w * 0.15, lo + w * 0.18, lo + w * 0.15, lo + w * 0.55)
        bell.lineTo(lo + w * 0.08, lo + w * 0.70)
        bell.lineTo(hi - w * 0.08, lo + w * 0.70)
        bell.lineTo(hi - w * 0.15, lo + w * 0.55)
        bell.quadTo(hi - w * 0.15, lo + w * 0.18, mid, lo + w * 0.10)
        bell.closeSubpath()
        p.drawPath(bell)
        p.drawEllipse(QPointF(mid, hi - w * 0.15), w * 0.08, w * 0.08)
        p.drawEllipse(QPointF(mid, lo + w * 0.08), w * 0.05, w * 0.05)

    def _draw_search(self, p, lo, hi, c):
        mid = (lo + hi) / 2
        w = hi - lo
        r = w * 0.26
        cx, cy = mid - w * 0.06, mid - w * 0.06
        p.setPen(QPen(c, 2.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)
        hx = cx + r * 0.707
        hy = cy + r * 0.707
        p.setPen(QPen(c, 2.5))
        p.drawLine(QPointF(hx, hy), QPointF(hi - w * 0.05, hi - w * 0.05))

    def _draw_location(self, p, lo, hi, c):
        mid = (lo + hi) / 2
        w = hi - lo
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        pin = QPainterPath()
        pin.moveTo(mid, hi - w * 0.08)
        pin.quadTo(lo + w * 0.15, mid, lo + w * 0.20, lo + w * 0.32)
        pin.arcTo(QRectF(lo + w * 0.20, lo + w * 0.08, w * 0.60, w * 0.48), 210, -240)
        pin.quadTo(hi - w * 0.15, mid, mid, hi - w * 0.08)
        pin.closeSubpath()
        p.drawPath(pin)
        # inner circle
        p.setBrush(QColor(0, 0, 0, 0))
        p.save()
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        p.drawEllipse(QPointF(mid, lo + w * 0.32), w * 0.09, w * 0.09)
        p.restore()

    def _draw_fallback(self, p, lo, hi, c):
        mid = (lo + hi) / 2
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(mid, mid), (hi - lo) * 0.3, (hi - lo) * 0.3)


# ══════════════════════════════════════════════════════════════════
#  PAINTED BACKGROUND WIDGETS
# ══════════════════════════════════════════════════════════════════

class BannerWidget(QFrame):
    """Banner that uses 'Background di dashboard.jpg' only."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_pixmap = None
        fp = os.path.join(BASE_DIR, "Background di dashboard.jpg")
        if os.path.exists(fp):
            self.bg_pixmap = QPixmap(fp)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 22, 22)
        painter.setClipPath(clip)

        if self.bg_pixmap and not self.bg_pixmap.isNull():
            scaled = self.bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            g = QLinearGradient(0, 0, self.width(), 0)
            g.setColorAt(0, QColor(26, 60, 42))
            g.setColorAt(1, QColor(45, 107, 74))
            painter.fillRect(self.rect(), g)

        overlay = QLinearGradient(0, self.height() * 0.40, 0, self.height())
        overlay.setColorAt(0, QColor(0, 0, 0, 0))
        overlay.setColorAt(1, QColor(0, 0, 0, 100))
        painter.fillRect(self.rect(), overlay)
        painter.end()


class ImageCardWidget(QFrame):
    """Card with a full background image and rounded corners."""

    def __init__(self, image_file, parent=None):
        super().__init__(parent)
        self.bg_pixmap = None
        fp = os.path.join(BASE_DIR, image_file)
        if os.path.exists(fp):
            self.bg_pixmap = QPixmap(fp)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 18, 18)
        painter.setClipPath(clip)
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            scaled = self.bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.fillRect(self.rect(), QColor(60, 80, 65))
        painter.fillRect(self.rect(), QColor(0, 0, 0, 45))
        painter.end()


# ══════════════════════════════════════════════════════════════════
#  DASHBOARD PAGE
# ══════════════════════════════════════════════════════════════════

class DashboardPage(QWidget):
    logout_signal = pyqtSignal()
    navigate_sholat = pyqtSignal()
    navigate_quran = pyqtSignal()
    navigate_sedekah = pyqtSignal()
    navigate_settings = pyqtSignal()

    def __init__(self, db, user_data=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_name = "User"
        self.user_location = "Indonesia"
        self.user_provinsi = ""
        self.user_kabkota = ""
        self._prayer_data = {}  # jadwal shalat hari ini
        if user_data:
            self.user_name = user_data.get("nama_lengkap", "User")
            self.user_location = user_data.get("location", "Indonesia") or "Indonesia"
            self.user_provinsi = user_data.get("provinsi", "")
            self.user_kabkota = user_data.get("kabkota", "")

        # Load logo
        self.logo_pixmap = QPixmap(os.path.join(BASE_DIR, "logo.png"))

        self.setup_ui()
        self._start_clock()

    def set_user_data(self, data):
        if not data:
            return
        self.user_name = data.get("nama_lengkap", "User")
        self.user_location = data.get("location", "Indonesia") or "Indonesia"
        self.user_provinsi = data.get("provinsi", "")
        self.user_kabkota = data.get("kabkota", "")
        self.greeting_label.setText(f"Assalamu'alaikum, {self.user_name}.")
        self.loc_text.setText(f" {self.user_location} ∨")
        initials = "".join(w[0].upper() for w in self.user_name.split()[:2])
        self.avatar_label.setText(initials or "U")
        self._load_prayer_times()

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

        # Logo row — SVG image
        logo_row = QHBoxLayout()
        logo_row.setSpacing(10)
        logo_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        logo_img = QLabel()
        if self.logo_pixmap and not self.logo_pixmap.isNull():
            logo_img.setPixmap(self.logo_pixmap.scaled(
                44, 44,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            logo_img.setText("⌂")
            logo_img.setStyleSheet("color:#A8D5A2;font-size:28px;")
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

        # Menu items with vector icons
        menu_items = [
            ("home", "Dashboard", True),
            ("mosque", "Jadwal Sholat", False),
            ("book", "Al-Qur'an", False),
            ("chart", "Sedekah Tracker", False),
        ]
        self._sidebar_btns = {}
        for ic_name, label, active in menu_items:
            btn = self._sidebar_btn(ic_name, label, active)
            self._sidebar_btns[label] = btn
            lay.addWidget(btn)
            lay.addSpacing(4)

        # Navigation: Jadwal Sholat
        self._sidebar_btns["Jadwal Sholat"].mousePressEvent = lambda e: self.navigate_sholat.emit()
        self._sidebar_btns["Al-Qur'an"].mousePressEvent = lambda e: self.navigate_quran.emit()
        self._sidebar_btns["Sedekah Tracker"].mousePressEvent = lambda e: self.navigate_sedekah.emit()

        lay.addStretch()

        settings_btn = self._sidebar_btn("gear", "Settings", False)
        settings_btn.mousePressEvent = lambda e: self.navigate_settings.emit()
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
        col.setContentsMargins(28, 0, 28, 12)
        col.setSpacing(0)

        col.addWidget(self._top_bar())
        col.addSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        vb = QVBoxLayout(inner)
        vb.setContentsMargins(0, 0, 6, 0)
        vb.setSpacing(0)

        vb.addWidget(self._banner_with_prayers())
        vb.addSpacing(22)

        da = QLabel("Daily Activity")
        da.setStyleSheet("font-size:18px;font-weight:bold;color:#2D2D2D;background:transparent;")
        vb.addWidget(da)
        vb.addSpacing(14)
        vb.addLayout(self._cards_row())
        vb.addStretch()

        scroll.setWidget(inner)
        col.addWidget(scroll)
        return wrapper

    # ─────────────── TOP BAR ───────────────
    def _top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(60)
        bar.setStyleSheet("background:transparent;")

        h = QHBoxLayout(bar)
        h.setContentsMargins(0, 14, 0, 0)

        # Search bar
        search_wrap = QWidget()
        search_wrap.setFixedSize(280, 42)
        search_wrap.setStyleSheet("background-color:#E2E4DD;border-radius:21px;")
        sw_h = QHBoxLayout(search_wrap)
        sw_h.setContentsMargins(16, 0, 16, 0)
        sw_h.setSpacing(8)
        search_ic = IconWidget("search", 18, QColor("#999"))
        sw_h.addWidget(search_ic)
        search_input = QLineEdit()
        search_input.setPlaceholderText("Explore")
        search_input.setStyleSheet(
            "QLineEdit{background:transparent;border:none;font-size:13px;color:#555;}"
            "QLineEdit::placeholder{color:#999;}"
        )
        sw_h.addWidget(search_input)
        h.addWidget(search_wrap)
        h.addStretch()

        bell_ic = IconWidget("bell", 24, QColor("#D4A745"))
        h.addWidget(bell_ic)
        h.addSpacing(20)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(42, 42)
        initials = "".join(w[0].upper() for w in self.user_name.split()[:2])
        self.avatar_label.setText(initials or "U")
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet("""
            QLabel {
                background-color: #B0C4A8;
                border-radius: 21px;
                font-size: 14px;
                font-weight: bold;
                color: #1A3C2A;
            }
        """)
        h.addWidget(self.avatar_label)
        h.addSpacing(4)
        arrow = QLabel("▾")
        arrow.setStyleSheet("font-size:13px;color:#777;background:transparent;")
        h.addWidget(arrow)
        return bar

    # ─────────────── BANNER + PRAYER ROW ───────────────
    def _banner_with_prayers(self):
        banner = BannerWidget()
        banner.setFixedHeight(280)

        main_lay = QVBoxLayout(banner)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Greeting + Clock ──
        top = QWidget()
        top.setStyleSheet("background:transparent;")
        top_h = QHBoxLayout(top)
        top_h.setContentsMargins(32, 24, 32, 0)

        left = QVBoxLayout()
        left.setSpacing(6)
        self.greeting_label = QLabel(f"Assalamu'alaikum, {self.user_name}.")
        self.greeting_label.setStyleSheet(
            "color:#FFF;font-size:26px;font-weight:bold;background:transparent;"
        )
        left.addWidget(self.greeting_label)

        loc_row = QHBoxLayout()
        loc_row.setSpacing(4)
        loc_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        loc_ic = IconWidget("location", 16, QColor(255, 255, 255, 190))
        loc_row.addWidget(loc_ic)
        self.loc_text = QLabel(f" {self.user_location}")
        self.loc_text.setStyleSheet("color:rgba(255,255,255,190);font-size:13px;background:transparent;")
        loc_row.addWidget(self.loc_text)
        left.addLayout(loc_row)
        left.addStretch()
        top_h.addLayout(left)
        top_h.addStretch()

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.clock_label = QLabel(datetime.now().strftime("%H:%M:%S"))
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.clock_label.setStyleSheet(
            "color:rgba(255,255,255,160);font-size:58px;font-weight:bold;background:transparent;"
        )
        right.addWidget(self.clock_label)
        crescent_row = QHBoxLayout()
        crescent_row.setAlignment(Qt.AlignmentFlag.AlignRight)
        crescent = IconWidget("crescent", 26, QColor("#FFD88E"))
        crescent_row.addWidget(crescent)
        right.addLayout(crescent_row)
        top_h.addLayout(right)

        main_lay.addWidget(top, 1)

        # ── "Waktu Sholat" pill ──
        pill_row = QHBoxLayout()
        pill_row.setContentsMargins(0, 0, 0, 0)
        pill_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pill = QLabel("Waktu Sholat")
        pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pill.setFixedSize(140, 32)
        pill.setStyleSheet("""
            QLabel {
                background-color: rgba(45, 107, 74, 220);
                color: #FFFFFF;
                border-radius: 16px;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
        """)
        pill_row.addWidget(pill)
        main_lay.addLayout(pill_row)
        main_lay.addSpacing(4)

        # ── Prayer times row ──
        prayer_container = QWidget()
        prayer_container.setStyleSheet("background:transparent;")
        prayer_h = QHBoxLayout(prayer_container)
        prayer_h.setContentsMargins(16, 0, 16, 14)
        prayer_h.setSpacing(6)

        # Build prayer item widgets with placeholder times
        self._prayer_labels = {}
        prayers_def = [
            ("sunrise", "Subuh", "--:--", "subuh"),
            ("sun", "Dzuhur", "--:--", "dzuhur"),
            ("cloud_sun", "Ashar", "--:--", "ashar"),
            ("sunset", "Maghrib", "--:--", "maghrib"),
            ("moon", "Isya", "--:--", "isya"),
        ]
        for idx, (ic_name, name, t, key) in enumerate(prayers_def):
            frame, time_label = self._prayer_item_dynamic(ic_name, name, t, False)
            self._prayer_labels[key] = time_label
            prayer_h.addWidget(frame)

        main_lay.addWidget(prayer_container)
        return banner

    def _prayer_item_dynamic(self, icon_name, name, time_str, active=False):
        """Create a prayer item frame and return (frame, time_label) for dynamic updates."""
        f = QFrame()
        f.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        f.setFixedHeight(80)
        if active:
            f.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 22);
                    border-radius: 18px;
                    border: 1px solid rgba(255,255,255,25);
                }
            """)
        else:
            f.setStyleSheet("QFrame{background:transparent;border-radius:18px;}")

        v = QVBoxLayout(f)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(3)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ic = IconWidget(icon_name, 28, QColor("#FFFFFF"))
        ic_h = QHBoxLayout()
        ic_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic_h.addWidget(ic)
        v.addLayout(ic_h)

        nm = QLabel(name)
        nm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nm.setStyleSheet("font-size:12px;color:#FFF;font-weight:normal;background:transparent;")
        v.addWidget(nm)

        tm = QLabel(time_str)
        tm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tm.setStyleSheet("font-size:10px;color:rgba(255,255,255,150);background:transparent;")
        v.addWidget(tm)

        return f, tm

    # ─────────────── PRAYER TIMES API ───────────────
    def _load_prayer_times(self):
        """Fetch prayer times from equran.id API in background thread."""
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
        """Apply fetched prayer times to the dashboard labels."""
        self._prayer_data = jadwal
        mapping = {
            "subuh": jadwal.get("subuh", "--:--"),
            "dzuhur": jadwal.get("dzuhur", "--:--"),
            "ashar": jadwal.get("ashar", "--:--"),
            "maghrib": jadwal.get("maghrib", "--:--"),
            "isya": jadwal.get("isya", "--:--"),
        }
        for key, time_str in mapping.items():
            if key in self._prayer_labels:
                self._prayer_labels[key].setText(time_str)

        # Highlight active prayer based on current time
        self._update_active_prayer()

    def _update_active_prayer(self):
        """Highlight the current/upcoming prayer based on actual times."""
        if not self._prayer_data:
            return
        now_min = datetime.now().hour * 60 + datetime.now().minute
        keys = ["subuh", "dzuhur", "ashar", "maghrib", "isya"]
        times_min = []
        for k in keys:
            t = self._prayer_data.get(k, "00:00")
            try:
                h, m = t.split(":")
                times_min.append(int(h) * 60 + int(m))
            except Exception:
                times_min.append(0)

        active_idx = len(keys) - 1
        for i, tm in enumerate(times_min):
            if now_min < tm:
                active_idx = max(0, i - 1) if i > 0 else 0
                break

        # Update styles on prayer frames
        prayer_container = list(self._prayer_labels.values())[0].parent().parent() if self._prayer_labels else None
        if prayer_container:
            frames = [self._prayer_labels[k].parent() for k in keys if k in self._prayer_labels]
            for i, f in enumerate(frames):
                if i == active_idx:
                    f.setStyleSheet("""
                        QFrame {
                            background: rgba(255, 255, 255, 22);
                            border-radius: 18px;
                            border: 1px solid rgba(255,255,255,25);
                        }
                    """)
                else:
                    f.setStyleSheet("QFrame{background:transparent;border-radius:18px;}")

    # ─────────────── CARDS ROW ───────────────
    def _cards_row(self):
        h = QHBoxLayout()
        h.setSpacing(16)
        h.addWidget(self._progress_card(), 3)
        right_col = QVBoxLayout()
        right_col.setSpacing(14)
        right_col.addWidget(self._sedekah_card())
        right_col.addWidget(self._tadarus_card())
        h.addLayout(right_col, 2)
        return h

    def _progress_card(self):
        card = QFrame()
        card.setObjectName("progressCard")
        card.setStyleSheet("""
            QFrame#progressCard {
                background: #FFFFFF;
                border-radius: 18px;
                border: 1px solid rgba(0,0,0,8);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 18))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        v = QVBoxLayout(card)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(20)
        for label, pct, color in [
            ("Konsistensi Sholat", 90, "#2D6B4A"),
            ("Konsistensi Tadarus", 70, "#3A8D5E"),
            ("Konsistensi Sedekah", 80, "#4AA06C"),
        ]:
            v.addWidget(self._progress_row(label, pct, color))
        v.addStretch()
        return card

    def _progress_row(self, label, pct, color):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        top = QHBoxLayout()
        nm = QLabel(label)
        nm.setStyleSheet("font-size:13px;color:#444;font-weight:bold;background:transparent;")
        top.addWidget(nm)
        top.addStretch()
        pc = QLabel(f"{pct}%")
        pc.setStyleSheet("font-size:13px;color:#444;font-weight:bold;background:transparent;")
        top.addWidget(pc)
        v.addLayout(top)
        bar = QProgressBar()
        bar.setValue(pct)
        bar.setTextVisible(False)
        bar.setFixedHeight(12)
        bar.setStyleSheet(f"""
            QProgressBar {{background:#E4E8DE;border:none;border-radius:6px;}}
            QProgressBar::chunk {{background:{color};border-radius:6px;}}
        """)
        v.addWidget(bar)
        return w

    def _sedekah_card(self):
        card = ImageCardWidget("background sedekah.jpg")
        card.setFixedHeight(120)
        card.setStyleSheet("")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 3)
        card.setGraphicsEffect(shadow)
        v = QVBoxLayout(card)
        v.setContentsMargins(22, 16, 22, 16)
        v.setSpacing(4)
        title = QLabel("Sedekah Minggu Ini")
        title.setStyleSheet("color:rgba(255,255,255,210);font-size:12px;background:transparent;")
        v.addWidget(title)
        value = QLabel("Rp 20.000,00")
        value.setStyleSheet("color:#FFF;font-size:26px;font-weight:bold;background:transparent;")
        v.addWidget(value)
        v.addStretch()
        return card

    def _tadarus_card(self):
        card = ImageCardWidget("background quran.jpg")
        card.setFixedHeight(120)
        card.setStyleSheet("")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 3)
        card.setGraphicsEffect(shadow)
        v = QVBoxLayout(card)
        v.setContentsMargins(22, 16, 22, 16)
        v.setSpacing(4)
        title = QLabel("Tadarus Hari Ini")
        title.setStyleSheet("color:rgba(255,255,255,210);font-size:12px;background:transparent;")
        v.addWidget(title)
        value = QLabel("Q.S An-Nur 64:2")
        value.setStyleSheet("color:#FFF;font-size:22px;font-weight:bold;background:transparent;")
        v.addWidget(value)
        link = QLabel("Lanjutkan Membaca...")
        link.setStyleSheet("color:rgba(255,255,255,180);font-size:11px;background:transparent;")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        v.addWidget(link)
        v.addStretch()
        return card

    # ─────────────── CLOCK ───────────────
    def _start_clock(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

    def _tick(self):
        self.clock_label.setText(datetime.now().strftime("%H:%M"))
