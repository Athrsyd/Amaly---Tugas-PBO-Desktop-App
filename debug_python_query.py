#!/usr/bin/env python3
"""Debug query dari Python dengan parametersiasi sama seperti database.py"""

import sqlite3

db_path = "d:\\Alif\\SMK\\DPK\\CODE\\Desktop App\\amalan_harian.db"
conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

# Test query EXACTLY seperti di database.py get_sedekah_bulan
user_id  = 4
bulan = 4
tahun = 2026
bulan_str = f"{bulan:02d}"
tahun_str = str(tahun)

print(f"Parameters: user_id={user_id}, bulan_str={bulan_str!r}, tahun_str={tahun_str!r}")

# Query EXACTLY seperti di database.py
print("\n=== Executing query (dengan %%m dan %%Y) ===")
cursor.execute(
    """SELECT * FROM sedekah
       WHERE user_id = ?
         AND strftime('%%m', tanggal) = ?
         AND strftime('%%Y', tanggal) = ?
       ORDER BY tanggal""",
    (user_id, bulan_str, tahun_str)
)
rows = cursor.fetchall()
print(f"Rows found: {len(rows)}")
for row in rows:
    print(f"  {dict(row)}")

# Debug: cek apa hasil strftime untuk user_id=4
print("\n=== Debug: All strftime results for user_id=4 ===")
cursor.execute("SELECT id, tanggal, strftime('%m', tanggal) as m, strftime('%Y', tanggal) as y FROM sedekah WHERE user_id=4")
for row in cursor.fetchall():
    print(f"  id={row['id']}, tanggal={row['tanggal']}, m={row['m']!r}, y={row['y']!r}")

conn.close()
