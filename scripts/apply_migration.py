"""Aplica migrations al Supabase existente."""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_REF = os.environ.get("SUPABASE_PROJECT_REF", "wicnndedakeuvxkzmelz")
ACCESS_TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN")
if not ACCESS_TOKEN:
    raise SystemExit("SUPABASE_ACCESS_TOKEN no configurado")


def run_sql(sql):
    url = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
    payload = json.dumps({"query": sql}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "mundial-cli/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def main():
    root = Path(__file__).parent.parent
    migrations = sorted((root / "infra/supabase/migrations").glob("*.sql"))
    for m in migrations:
        print(f"-> {m.name}")
        s, b = run_sql(m.read_text(encoding="utf-8"))
        if s >= 300:
            print(f"   FAIL ({s})")
            print(b[:800])
            sys.exit(1)
        print(f"   OK")
    # Verify
    s, b = run_sql("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name LIKE 'wc_%'
        ORDER BY table_name;
    """)
    print("\nTablas wc_* creadas:")
    print(b)


if __name__ == "__main__":
    main()
