import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import sqlite3
con = sqlite3.connect(str(BASE_DIR / 'nexora.db'))
cur = con.cursor()
for row in cur.execute('SELECT id, conversation_id, role, content FROM messages ORDER BY created_at DESC LIMIT 6'):
    print(f"[{row[2]}] id={row[0]}")
    print(row[3].encode('ascii', 'replace').decode('ascii'))
    print("="*60)
con.close()
