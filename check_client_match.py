import sqlite3

conn = sqlite3.connect('data/receipts.db')
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT firm_id, client_id, email_from, filename FROM receipts ORDER BY created_at').fetchall()

print('=== Client ID Matching Results ===')
print()
for row in rows:
    print(f'{row["firm_id"]:12} {row["client_id"]:12} {row["email_from"]:35} {row["filename"][:40]}')

conn.close()
