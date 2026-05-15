import sqlite3

conn = sqlite3.connect('data/receipts.db')
conn.row_factory = sqlite3.Row

print('=== Unique firm_id and client_id values ===')
rows = conn.execute('SELECT firm_id, client_id, COUNT(*) as count FROM receipts GROUP BY firm_id, client_id').fetchall()
for row in rows:
    print(f'  firm_id={row["firm_id"]}, client_id={row["client_id"]}, count={row["count"]}')

print()
print('=== All receipts (firm_id, client_id, filename) ===')
rows = conn.execute('SELECT firm_id, client_id, filename FROM receipts ORDER BY created_at').fetchall()
for row in rows:
    print(f'  {row["firm_id"]:12} {row["client_id"]:10} {row["filename"]}')

conn.close()
