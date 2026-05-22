"""Carga tournament_outcomes + top_scorers + actualiza predictions y simulations a Supabase."""
import json, os, sys, urllib.request, urllib.error
from pathlib import Path

SUPABASE_URL = os.environ["NEXT_PUBLIC_SUPABASE_URL"].rstrip("/")
SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
PROJECT_REF = os.environ["SUPABASE_PROJECT_REF"]
MGMT_TOKEN = os.environ["SUPABASE_ACCESS_TOKEN"]


def rest_upsert(table, rows, on_conflict):
    url = f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={on_conflict}"
    body = json.dumps(rows, default=str).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json", "Prefer": "return=minimal,resolution=merge-duplicates",
        "User-Agent": "mundial/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def mgmt_sql(sql):
    url = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
    req = urllib.request.Request(url, data=json.dumps({"query": sql}).encode(), method="POST",
                                  headers={"Authorization": f"Bearer {MGMT_TOKEN}", "Content-Type": "application/json", "User-Agent": "mundial/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    out = Path(__file__).parent.parent / "data" / "output"

    # 1) Update predictions (re-load with new v2 scorelines)
    s, b = mgmt_sql("SELECT id, match_number FROM wc_matches ORDER BY match_number;")
    if s >= 300:
        print(f"err: {b[:200]}"); sys.exit(1)
    match_ids = {row["match_number"]: row["id"] for row in json.loads(b)}

    preds_raw = json.loads((out / "predictions.json").read_text(encoding="utf-8"))
    preds = []
    for p in preds_raw:
        if p["match_number"] not in match_ids:
            continue
        preds.append({
            "match_id": match_ids[p["match_number"]],
            "model_version": "v2",
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
    print(f"predictions v2: {s} - {len(preds)} rows")
    if s >= 300:
        print(b[:300])

    # 2) Simulations v2
    sims = json.loads((out / "simulations.json").read_text(encoding="utf-8"))
    for s_row in sims:
        s_row["model_version"] = "v2"
    s, b = rest_upsert("wc_simulations", sims, "team_code,model_version")
    print(f"simulations v2: {s} - {len(sims)} rows")

    # 3) Tournament outcomes (podio)
    outcomes = json.loads((out / "tournament_outcomes.json").read_text(encoding="utf-8"))
    s, b = rest_upsert("wc_tournament_outcomes", outcomes, "team_code,model_version")
    print(f"tournament_outcomes: {s} - {len(outcomes)} rows")
    if s >= 300:
        print(b[:300])

    # 4) Top scorers
    scorers = json.loads((out / "top_scorers.json").read_text(encoding="utf-8"))
    for sc in scorers:
        sc["model_version"] = "v2"
    s, b = rest_upsert("wc_top_scorers", scorers, "player_name,team_code,model_version")
    print(f"top_scorers: {s} - {len(scorers)} rows")
    if s >= 300:
        print(b[:300])

    # Verify
    s, b = mgmt_sql("""
        SELECT 'wc_predictions v1' AS t, COUNT(*) AS n FROM wc_predictions WHERE model_version='v1'
        UNION ALL SELECT 'wc_predictions v2', COUNT(*) FROM wc_predictions WHERE model_version='v2'
        UNION ALL SELECT 'wc_simulations v2', COUNT(*) FROM wc_simulations WHERE model_version='v2'
        UNION ALL SELECT 'wc_tournament_outcomes', COUNT(*) FROM wc_tournament_outcomes
        UNION ALL SELECT 'wc_top_scorers', COUNT(*) FROM wc_top_scorers
        ORDER BY t;
    """)
    print("\nCounts:")
    print(b)


if __name__ == "__main__":
    main()
