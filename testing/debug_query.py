#!/usr/bin/env python3
import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
db_path = os.path.join(BASE_DIR, "amalan_harian.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Test query dengan parameter yang sama seperti di aplikasi
cursor.execute(
    """SELECT * FROM sedekah WHERE user_id = ? AND strftime('%%m', tanggal) = ? AND strftime('%%Y', tanggal) = ?""",
    (4, "03", "2026")
)

rows = cursor.fetchall()
print(f"Query with params (4, '03', '2026'): {len(rows)} rows found")
for row in rows:
    print(f"  {row}")

# Test dengan bulan dan tahun integer
cursor.execute(
    """SELECT * FROM sedekah WHERE user_id = ? AND strftime('%%m', tanggal) = ? AND strftime('%%Y', tanggal) = ?""",
    (4, f"{3:02d}", str(2026))
)

rows2 = cursor.fetchall()
print(f"\nQuery with params (4, '{3:02d}', '{2026}'): {len(rows2)} rows found")
for row in rows2:
    print(f"  {row}")

conn.close()
