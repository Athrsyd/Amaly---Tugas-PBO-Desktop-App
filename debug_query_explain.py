#!/usr/bin/env python3
"""Debug query explanation dan plan"""

import sqlite3

db_path = "d:\\Alif\\SMK\\DPK\\CODE\\Desktop App\\amalan_harian.db"
conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

user_id  = 4
bulan_str = "04"
tahun_str = "2026"

print("=== Query EXPLAIN QUERY PLAN ===")
cursor.execute(
    """EXPLAIN QUERY PLAN
       SELECT * FROM sedekah
       WHERE user_id = ?
         AND strftime('%%m', tanggal) = ?
         AND strftime('%%Y', tanggal) = ?
       ORDER BY tanggal""",
    (user_id, bulan_str, tahun_str)
)
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Test query tanpa parameter
print("\n=== Query dengan nilai hardcoded ===")
cursor.execute(
    f"""SELECT * FROM sedekah
       WHERE user_id = 4
         AND strftime('%m', tanggal) = '04'
         AND strftime('%Y', tanggal) = '2026'
       ORDER BY tanggal"""
)
rows = cursor.fetchall()
print(f"Rows found: {len(rows)}")
for row in rows:
    print(f"  {dict(row)}")

# Test query dengan parameter tapi print buat debugging
print("\n=== Debug cast parameter ===")
print(f"Parameter types: user_id={type(user_id).__name__}, bulan_str={type(bulan_str).__name__}, tahun_str={type(tahun_str).__name__}")
print(f"Parameter values: user_id={user_id!r}, bulan_str={bulan_str!r}, tahun_str={tahun_str!r}")
print(f"str(4)={str(4)!r}, str(4) == '04'? {str(4) == '04'}")
print(f"f'{4:02d}'={f'{4:02d}'!r}")

# Try dengan integer convert
print("\n=== Query dengan explicit string conversion ===")
cursor.execute(
    """SELECT * FROM sedekah
       WHERE user_id = ?
         AND strftime('%m', tanggal) = ?
         AND strftime('%Y', tanggal) = ?
       ORDER BY tanggal""",
    (int(user_id), str(bulan_str), str(tahun_str))
)
rows = cursor.fetchall()
print(f"Rows found: {len(rows)}")

conn.close()
