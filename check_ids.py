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

print()
print('=== Orphaned categorisations.extraction_id (no matching row in extractions) ===')
rows = conn.execute('''
    SELECT c.categorisation_id, c.receipt_id, c.extraction_id, c.categorised_at
    FROM categorisations c
    LEFT JOIN extractions e ON c.extraction_id = e.extraction_id
    WHERE e.extraction_id IS NULL
''').fetchall()
if rows:
    print(f'  FOUND {len(rows)} orphaned row(s):')
    for row in rows:
        print(f'    categorisation_id={row["categorisation_id"]} receipt_id={row["receipt_id"]} '
              f'extraction_id={row["extraction_id"]} categorised_at={row["categorised_at"]}')
else:
    print('  none found')

conn.close()
