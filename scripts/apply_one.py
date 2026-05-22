"""Aplica UNA migration."""
import json, os, sys, urllib.request
from pathlib import Path

if len(sys.argv) < 2:
    print("Uso: python scripts/apply_one.py <ruta_sql>"); sys.exit(1)

sql = Path(sys.argv[1]).read_text(encoding="utf-8")
url = f'https://api.supabase.com/v1/projects/{os.environ["SUPABASE_PROJECT_REF"]}/database/query'
req = urllib.request.Request(
    url, data=json.dumps({"query": sql}).encode(), method="POST",
    headers={
        "Authorization": f'Bearer {os.environ["SUPABASE_ACCESS_TOKEN"]}',
        "Content-Type": "application/json", "User-Agent": "mundial/1.0",
    },
)
try:
    r = urllib.request.urlopen(req, timeout=60)
    print(f"Apply {sys.argv[1]}: HTTP {r.status} OK")
except urllib.error.HTTPError as e:
    print(f"ERROR HTTP {e.code}: {e.read().decode()}")
