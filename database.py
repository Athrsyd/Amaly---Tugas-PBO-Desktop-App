"""
Database module untuk Aplikasi Amalan Harian
Mengelola koneksi SQLite dan operasi CRUD untuk users dan amalan
"""

import sqlite3
import hashlib
import os
from datetime import datetime, date


class Database:
    """Kelas untuk mengelola database SQLite aplikasi Amalan Harian"""

    def __init__(self, db_name="amalan_harian.db"):
        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), db_name
        )
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        """Membuat tabel-tabel yang diperlukan jika belum ada"""
        cursor = self.conn.cursor()

        # Tabel Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_lengkap TEXT NOT NULL,
                location TEXT DEFAULT '',
                provinsi TEXT DEFAULT '',
                kabkota TEXT DEFAULT '',
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Migrasi: tambah kolom provinsi & kabkota jika belum ada
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN provinsi TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN kabkota TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

        # Tabel Amalan
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS amalan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                jenis_amalan TEXT NOT NULL,
                keterangan TEXT,
                tanggal DATE NOT NULL,
                waktu TIME,
                status TEXT DEFAULT 'selesai',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Tabel Reminder
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                judul TEXT NOT NULL,
                waktu TIME NOT NULL,
                aktif INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Tabel Checklist Sholat Fardhu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sholat_checklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tanggal DATE NOT NULL,
                subuh INTEGER DEFAULT 0,
                dzuhur INTEGER DEFAULT 0,
                ashar INTEGER DEFAULT 0,
                maghrib INTEGER DEFAULT 0,
                isya INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, tanggal)
            )
        ''')

        # Tabel Bookmark / Baca Terakhir Al-Qur'an
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quran_bookmark (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                surat_nomor INTEGER NOT NULL,
                surat_nama TEXT NOT NULL,
                ayat_nomor INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id)
            )
        ''')

        # Tabel Target Baca Al-Qur'an
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quran_target (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                start_surat INTEGER NOT NULL,
                start_ayat INTEGER NOT NULL,
                end_surat INTEGER NOT NULL,
                end_ayat INTEGER NOT NULL,
                start_surat_nama TEXT DEFAULT '',
                end_surat_nama TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id)
            )
        ''')

        # Tabel Ayat yang Disukai
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quran_liked (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                surat_nomor INTEGER NOT NULL,
                surat_nama TEXT NOT NULL,
                ayat_nomor INTEGER NOT NULL,
                teks_arab TEXT DEFAULT '',
                teks_indonesia TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, surat_nomor, ayat_nomor)
            )
        ''')

        # Tabel Sedekah
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sedekah (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tanggal DATE NOT NULL,
                nominal REAL NOT NULL,
                kategori TEXT NOT NULL,
                keterangan TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Tabel Target Sedekah Bulanan
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sedekah_target (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                bulan INTEGER NOT NULL,
                tahun INTEGER NOT NULL,
                target_nominal REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, bulan, tahun)
            )
        ''')

        # Tabel User Settings / Preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, key)
            )
        ''')

        self.conn.commit()

    # ===================== PASSWORD HASHING =====================
    def hash_password(self, password):
        """Hash password menggunakan SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    # ===================== USER OPERATIONS =====================
    def register_user(self, nama_lengkap, location, password, provinsi="", kabkota=""):
        """Mendaftarkan user baru ke database"""
        try:
            cursor = self.conn.cursor()
            hashed = self.hash_password(password)
            username = nama_lengkap.strip().lower().replace(' ', '_')
            cursor.execute(
                "INSERT INTO users (nama_lengkap, location, provinsi, kabkota, username, password) VALUES (?, ?, ?, ?, ?, ?)",
                (nama_lengkap, location, provinsi, kabkota, username, hashed)
            )
            self.conn.commit()
            return True, "Registration successful!"
        except sqlite3.IntegrityError:
            return False, "Name already registered!"

    def login_user(self, name, password):
        """Autentikasi login user"""
        cursor = self.conn.cursor()
        hashed = self.hash_password(password)
        username = name.strip().lower().replace(' ', '_')
        cursor.execute(
            "SELECT * FROM users WHERE (nama_lengkap = ? OR username = ?) AND password = ?",
            (name, username, hashed)
        )
        user = cursor.fetchone()
        if user:
            return True, dict(user)
        return False, "Username atau password salah!"

    def get_user_by_id(self, user_id):
        """Mendapatkan data user berdasarkan ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None

    # ===================== AMALAN OPERATIONS =====================
    def add_amalan(self, user_id, jenis_amalan, keterangan="", tanggal=None, waktu=None):
        """Menambahkan catatan amalan baru"""
        if tanggal is None:
            tanggal = date.today().isoformat()
        if waktu is None:
            waktu = datetime.now().strftime("%H:%M")

        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO amalan (user_id, jenis_amalan, keterangan, tanggal, waktu) VALUES (?, ?, ?, ?, ?)",
            (user_id, jenis_amalan, keterangan, tanggal, waktu)
        )
        self.conn.commit()
        return True

    def get_amalan_today(self, user_id):
        """Mendapatkan semua amalan hari ini untuk user tertentu"""
        cursor = self.conn.cursor()
        today = date.today().isoformat()
        cursor.execute(
            "SELECT * FROM amalan WHERE user_id = ? AND tanggal = ? ORDER BY created_at DESC",
            (user_id, today)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_amalan_count_today(self, user_id, jenis=None):
        """Menghitung jumlah amalan hari ini, bisa difilter berdasarkan jenis"""
        cursor = self.conn.cursor()
        today = date.today().isoformat()
        if jenis:
            cursor.execute(
                "SELECT COUNT(*) as count FROM amalan WHERE user_id = ? AND tanggal = ? AND jenis_amalan = ?",
                (user_id, today, jenis)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) as count FROM amalan WHERE user_id = ? AND tanggal = ?",
                (user_id, today)
            )
        return cursor.fetchone()['count']

    def get_total_amalan(self, user_id):
        """Menghitung total semua amalan user"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM amalan WHERE user_id = ?",
            (user_id,)
        )
        return cursor.fetchone()['count']

    def get_amalan_stats(self, user_id):
        """Mendapatkan statistik amalan per jenis untuk hari ini"""
        cursor = self.conn.cursor()
        today = date.today().isoformat()
        cursor.execute(
            """SELECT jenis_amalan, COUNT(*) as count 
               FROM amalan 
               WHERE user_id = ? AND tanggal = ? 
               GROUP BY jenis_amalan""",
            (user_id, today)
        )
        stats = {}
        for row in cursor.fetchall():
            stats[row['jenis_amalan']] = row['count']
        return stats

    def get_weekly_stats(self, user_id):
        """Mendapatkan statistik amalan 7 hari terakhir"""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT tanggal, COUNT(*) as count 
               FROM amalan 
               WHERE user_id = ? AND tanggal >= date('now', '-7 days')
               GROUP BY tanggal 
               ORDER BY tanggal""",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def delete_amalan(self, amalan_id):
        """Menghapus amalan berdasarkan ID"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM amalan WHERE id = ?", (amalan_id,))
        self.conn.commit()
        return True

    def update_amalan(self, amalan_id, jenis_amalan, keterangan):
        """Mengupdate data amalan"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE amalan SET jenis_amalan = ?, keterangan = ? WHERE id = ?",
            (jenis_amalan, keterangan, amalan_id)
        )
        self.conn.commit()
        return True

    def close(self):
        """Menutup koneksi database"""
        self.conn.close()

    # ===================== SHOLAT CHECKLIST =====================
    def get_sholat_today(self, user_id):
        """Get today's sholat checklist, create if not exists."""
        cursor = self.conn.cursor()
        today = date.today().isoformat()
        cursor.execute(
            "SELECT * FROM sholat_checklist WHERE user_id = ? AND tanggal = ?",
            (user_id, today)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        # Create new row for today
        cursor.execute(
            "INSERT INTO sholat_checklist (user_id, tanggal) VALUES (?, ?)",
            (user_id, today)
        )
        self.conn.commit()
        cursor.execute(
            "SELECT * FROM sholat_checklist WHERE user_id = ? AND tanggal = ?",
            (user_id, today)
        )
        return dict(cursor.fetchone())

    def toggle_sholat(self, user_id, sholat_name):
        """Toggle a sholat fardhu checklist (subuh/dzuhur/ashar/maghrib/isya)."""
        if sholat_name not in ("subuh", "dzuhur", "ashar", "maghrib", "isya"):
            return
        today = date.today().isoformat()
        self.get_sholat_today(user_id)  # ensure row exists
        cursor = self.conn.cursor()
        cursor.execute(
            f"SELECT {sholat_name} FROM sholat_checklist WHERE user_id = ? AND tanggal = ?",
            (user_id, today)
        )
        current = cursor.fetchone()[0]
        new_val = 0 if current else 1
        cursor.execute(
            f"UPDATE sholat_checklist SET {sholat_name} = ? WHERE user_id = ? AND tanggal = ?",
            (new_val, user_id, today)
        )
        self.conn.commit()
        return new_val

    def get_sholat_weekly(self, user_id):
        """Get sholat checklist for last 7 days."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT * FROM sholat_checklist 
               WHERE user_id = ? AND tanggal >= date('now', '-6 days')
               ORDER BY tanggal""",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # ===================== QURAN BOOKMARK =====================
    def set_bookmark(self, user_id, surat_nomor, surat_nama, ayat_nomor):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO quran_bookmark (user_id, surat_nomor, surat_nama, ayat_nomor)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   surat_nomor=excluded.surat_nomor,
                   surat_nama=excluded.surat_nama,
                   ayat_nomor=excluded.ayat_nomor,
                   created_at=CURRENT_TIMESTAMP""",
            (user_id, surat_nomor, surat_nama, ayat_nomor)
        )
        self.conn.commit()

    def get_bookmark(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM quran_bookmark WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ===================== QURAN TARGET =====================
    def set_target(self, user_id, start_surat, start_ayat, end_surat, end_ayat,
                   start_surat_nama="", end_surat_nama=""):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO quran_target (user_id, start_surat, start_ayat, end_surat, end_ayat,
                   start_surat_nama, end_surat_nama)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   start_surat=excluded.start_surat, start_ayat=excluded.start_ayat,
                   end_surat=excluded.end_surat, end_ayat=excluded.end_ayat,
                   start_surat_nama=excluded.start_surat_nama,
                   end_surat_nama=excluded.end_surat_nama,
                   created_at=CURRENT_TIMESTAMP""",
            (user_id, start_surat, start_ayat, end_surat, end_ayat,
             start_surat_nama, end_surat_nama)
        )
        self.conn.commit()

    def get_target(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM quran_target WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ===================== QURAN LIKED =====================
    def toggle_liked_ayat(self, user_id, surat_nomor, surat_nama, ayat_nomor,
                          teks_arab="", teks_indonesia=""):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM quran_liked WHERE user_id=? AND surat_nomor=? AND ayat_nomor=?",
            (user_id, surat_nomor, ayat_nomor)
        )
        row = cursor.fetchone()
        if row:
            cursor.execute("DELETE FROM quran_liked WHERE id=?", (row['id'],))
            self.conn.commit()
            return False  # unliked
        cursor.execute(
            """INSERT INTO quran_liked (user_id, surat_nomor, surat_nama, ayat_nomor,
                   teks_arab, teks_indonesia) VALUES (?,?,?,?,?,?)""",
            (user_id, surat_nomor, surat_nama, ayat_nomor, teks_arab, teks_indonesia)
        )
        self.conn.commit()
        return True  # liked

    def is_ayat_liked(self, user_id, surat_nomor, ayat_nomor):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM quran_liked WHERE user_id=? AND surat_nomor=? AND ayat_nomor=?",
            (user_id, surat_nomor, ayat_nomor)
        )
        return cursor.fetchone() is not None

    def get_liked_ayat(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM quran_liked WHERE user_id=? ORDER BY surat_nomor, ayat_nomor",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # ===================== SEDEKAH TRACKER =====================
    def add_sedekah(self, user_id, tanggal, nominal, kategori, keterangan=""):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO sedekah (user_id, tanggal, nominal, kategori, keterangan)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, tanggal, nominal, kategori, keterangan)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_sedekah_bulan(self, user_id, bulan, tahun):
        """Get all sedekah entries for a given month/year."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT * FROM sedekah
               WHERE user_id = ?
                 AND strftime('%%m', tanggal) = ?
                 AND strftime('%%Y', tanggal) = ?
               ORDER BY tanggal""",
            (user_id, f"{bulan:02d}", str(tahun))
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_total_sedekah_bulan(self, user_id, bulan, tahun):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT COALESCE(SUM(nominal), 0) as total FROM sedekah
               WHERE user_id = ?
                 AND strftime('%%m', tanggal) = ?
                 AND strftime('%%Y', tanggal) = ?""",
            (user_id, f"{bulan:02d}", str(tahun))
        )
        return cursor.fetchone()["total"]

    def get_sedekah_days(self, user_id, bulan, tahun):
        """Get distinct days that have sedekah entries in a month."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT DISTINCT tanggal FROM sedekah
               WHERE user_id = ?
                 AND strftime('%%m', tanggal) = ?
                 AND strftime('%%Y', tanggal) = ?""",
            (user_id, f"{bulan:02d}", str(tahun))
        )
        return [row["tanggal"] for row in cursor.fetchall()]

    def set_sedekah_target(self, user_id, bulan, tahun, target_nominal):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO sedekah_target (user_id, bulan, tahun, target_nominal)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, bulan, tahun) DO UPDATE SET
                   target_nominal=excluded.target_nominal""",
            (user_id, bulan, tahun, target_nominal)
        )
        self.conn.commit()

    def get_sedekah_target(self, user_id, bulan, tahun):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM sedekah_target WHERE user_id=? AND bulan=? AND tahun=?",
            (user_id, bulan, tahun)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_sedekah(self, sedekah_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sedekah WHERE id = ?", (sedekah_id,))
        self.conn.commit()

    # ===================== USER SETTINGS =====================
    def update_user_name(self, user_id, new_name):
        cursor = self.conn.cursor()
        new_username = new_name.strip().lower().replace(' ', '_')
        try:
            cursor.execute(
                "UPDATE users SET nama_lengkap = ?, username = ? WHERE id = ?",
                (new_name, new_username, user_id)
            )
            self.conn.commit()
            return True, "Nama berhasil diubah."
        except sqlite3.IntegrityError:
            return False, "Username sudah digunakan."

    def update_user_password(self, user_id, old_password, new_password):
        cursor = self.conn.cursor()
        old_hash = self.hash_password(old_password)
        cursor.execute(
            "SELECT id FROM users WHERE id = ? AND password = ?",
            (user_id, old_hash)
        )
        if not cursor.fetchone():
            return False, "Password lama salah."
        new_hash = self.hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (new_hash, user_id)
        )
        self.conn.commit()
        return True, "Password berhasil diubah."

    def update_user_location(self, user_id, provinsi, kabkota):
        cursor = self.conn.cursor()
        location = f"{kabkota}, {provinsi}" if kabkota and provinsi else provinsi or kabkota
        cursor.execute(
            "UPDATE users SET provinsi = ?, kabkota = ?, location = ? WHERE id = ?",
            (provinsi, kabkota, location, user_id)
        )
        self.conn.commit()

    def set_setting(self, user_id, key, value):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO user_settings (user_id, key, value)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value""",
            (user_id, key, str(value))
        )
        self.conn.commit()

    def get_setting(self, user_id, key, default=None):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT value FROM user_settings WHERE user_id = ? AND key = ?",
            (user_id, key)
        )
        row = cursor.fetchone()
        return row["value"] if row else default
