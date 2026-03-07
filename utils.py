"""
Utils - Fungsi utilitas untuk Aplikasi Amalan Harian
"""

import os
import re
import base64
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_banner_image(width=380, height=160):
    """
    Memuat gambar banner masjid dari file SVG.
    SVG berisi embedded PNG base64, jadi kita extract langsung.
    Returns QPixmap atau None jika gagal.
    """
    svg_path = os.path.join(BASE_DIR, "image 4 (2).svg")

    if not os.path.exists(svg_path):
        return None

    try:
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()

        # Extract base64 PNG data from SVG
        match = re.search(r'xlink:href="data:image/png;base64,([^"]+)"', svg_content)
        if match:
            base64_data = match.group(1)
            image_bytes = base64.b64decode(base64_data)

            pixmap = QPixmap()
            pixmap.loadFromData(image_bytes, "PNG")

            if not pixmap.isNull():
                return pixmap.scaled(
                    width, height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
    except Exception as e:
        print(f"Error loading banner: {e}")

    return None


def load_image(filename, width=None, height=None):
    """
    Memuat gambar PNG dari direktori aplikasi.
    Returns QPixmap atau None jika gagal.
    """
    img_path = os.path.join(BASE_DIR, filename)

    if not os.path.exists(img_path):
        return None

    pixmap = QPixmap(img_path)
    if pixmap.isNull():
        return None

    if width and height:
        return pixmap.scaled(
            width, height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    elif width:
        return pixmap.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)
    elif height:
        return pixmap.scaledToHeight(height, Qt.TransformationMode.SmoothTransformation)

    return pixmap


def get_asset_path(filename):
    """Mendapatkan path lengkap untuk file asset"""
    return os.path.join(BASE_DIR, filename)
