"""Carga teams, matches, predictions, simulations desde JSON al Supabase."""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
PROJECT_REF = os.environ.get("SUPABASE_PROJECT_REF", "wicnndedakeuvxkzmelz")
MGMT_TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN")

if not all([SUPABASE_URL, SERVICE_KEY]):
    raise SystemExit("Faltan vars de entorno")


def rest_upsert(table, rows, on_conflict):
    url = f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={on_conflict}"
    body = json.dumps(rows, default=str).encode()
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal,resolution=merge-duplicates",
            "User-Agent": "mundial/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def mgmt_sql(sql):
    url = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
    body = json.dumps({"query": sql}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {MGMT_TOKEN}", "Content-Type": "application/json",
        "User-Agent": "mundial/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    out = Path(__file__).parent.parent / "data" / "output"

    # Teams (filtrar columnas que existen en BD)
    teams_raw = json.loads((out / "teams.json").read_text(encoding="utf-8"))
    valid = {"code","name","flag_emoji","confederation","group_letter","group_position","is_host","fifa_rank","fifa_points","elo_rating","manager_name","is_debut"}
    teams = [{k: v for k, v in t.items() if k in valid} for t in teams_raw]
    s, b = rest_upsert("wc_teams", teams, "code")
    print(f"teams: {s} - {len(teams)} rows")
    if s >= 300:
        print(b[:300])

    # Matches
    matches = json.loads((out / "matches.json").read_text(encoding="utf-8"))
    s, b = rest_upsert("wc_matches", matches, "match_number")
    print(f"matches: {s} - {len(matches)} rows")
    if s >= 300:
        print(b[:300])

    # Predictions: need to add match_id, so use SQL approach
    # First, get match_ids
    s, b = mgmt_sql("SELECT id, match_number FROM wc_matches ORDER BY match_number;")
    if s >= 300:
        print(f"err: {b[:200]}")
        sys.exit(1)
    match_ids = {row["match_number"]: row["id"] for row in json.loads(b)}

    preds_raw = json.loads((out / "predictions.json").read_text(encoding="utf-8"))
    preds = []
    for p in preds_raw:
        if p["match_number"] not in match_ids:
            continue
        preds.append({
            "match_id": match_ids[p["match_number"]],
            "model_version": "v1",
            "prob_home_win": p["prob_home_win"],
            "prob_draw": p["prob_draw"],
            "prob_away_win": p["prob_away_win"],
            "expected_home_goals": p["expected_home_goals"],
            "expected_away_goals": p["expected_away_goals"],
            "predicted_winner_code": p["predicted_winner_code"],
            "predicted_scoreline": p["predicted_scoreline"],
            "reasons": p["reasons"],
        })
    s, b = rest_upsert("wc_predictions", preds, "match_id,model_version")
    print(f"predictions: {s} - {len(preds)} rows")
    if s >= 300:
        print(b[:300])

    # Simulations
    sims = json.loads((out / "simulations.json").read_text(encoding="utf-8"))
    for s_row in sims:
        s_row["model_version"] = "v1"
    s, b = rest_upsert("wc_simulations", sims, "team_code,model_version")
    print(f"simulations: {s} - {len(sims)} rows")
    if s >= 300:
        print(b[:300])

    # Verify
    s, b = mgmt_sql("""
        SELECT 'wc_teams' AS t, COUNT(*) AS n FROM wc_teams
        UNION ALL SELECT 'wc_matches', COUNT(*) FROM wc_matches
        UNION ALL SELECT 'wc_predictions', COUNT(*) FROM wc_predictions
        UNION ALL SELECT 'wc_simulations', COUNT(*) FROM wc_simulations
        ORDER BY t;
    """)
    print("\nCounts:")
    print(b)


if __name__ == "__main__":
    main()
