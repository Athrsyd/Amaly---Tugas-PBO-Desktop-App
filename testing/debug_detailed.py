#!/usr/bin/env python3
import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
db_path = os.path.join(BASE_DIR, "amalan_harian.db")
print(f"Database path: {db_path}")
print(f"File exists: {os.path.exists(db_path)}")
print(f"File size: {os.path.getsize(db_path)} bytes")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Cek semua data sedekah user_id=4
print("\n=== All sedekah data for user_id=4 ===")
cursor.execute("SELECT id, tanggal FROM sedekah WHERE user_id=4 ORDER BY tanggal DESC")
all_rows = cursor.fetchall()
print(f"Total rows: {len(all_rows)}")
for row in all_rows:
    print(f"  id={row[0]}, tanggal={row[1]}")

# Test query tanpa strftime
print("\n=== Query without strftime, just tanggal ===")
cursor.execute("SELECT * FROM sedekah WHERE user_id=4 AND tanggal LIKE '2026-03%'")
rows = cursor.fetchall()
print(f"Rows found: {len(rows)}")

# Test strftime di SELECT
print("\n=== Test strftime in SELECT ===")
cursor.execute("""SELECT tanggal, strftime('%m', tanggal), strftime('%Y', tanggal) FROM sedekah WHERE user_id=4""")
for row in cursor.fetchall():
    print(f"  tanggal={row[0]}, month={row[1]}, year={row[2]}, month_repr={repr(row[1])}, year_repr={repr(row[2])}")

# Test dengan WHERE clause menggunakan strftime
print("\n=== Test strftime in WHERE clause (hardcoded) ===")
cursor.execute("""SELECT * FROM sedekah WHERE user_id=4 AND strftime('%m', tanggal)='03' AND strftime('%Y', tanggal)='2026'""")
rows = cursor.fetchall()
print(f"Rows found: {len(rows)}")

# Test dengan parameter
print("\n=== Test strftime in WHERE clause (with parameters) ===")
cursor.execute("""SELECT * FROM sedekah WHERE user_id=? AND strftime('%m', tanggal)=? AND strftime('%Y', tanggal)=?""",
               (4, '03', '2026'))
rows = cursor.fetchall()
print(f"Rows found: {len(rows)}")

conn.close()
