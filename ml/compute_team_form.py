"""
Computa features avanzados por equipo desde martj42 (49K partidos):
- form_score: goal diff promedio últimos 10 partidos
- recent_elo_change: cambio de Elo últimos 12 meses
- wc_performance: rendimiento histórico en mundiales
- xg_proxy: goles esperados basados en históricos vs adversarios similares
- goal_avg / conceded_avg: goles a favor / en contra recientes

Salida: data/output/team_features.json
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw" / "martj42_results.csv"
OUT = ROOT / "data" / "output"

NAME_TO_CODE = {
    "Mexico": "MEX", "South Africa": "RSA", "South Korea": "KOR", "Czech Republic": "CZE", "Czechia": "CZE",
    "Canada": "CAN", "Bosnia and Herzegovina": "BIH", "Qatar": "QAT", "Switzerland": "SUI",
    "Brazil": "BRA", "Morocco": "MAR", "Haiti": "HAI", "Scotland": "SCO",
    "United States": "USA", "Paraguay": "PAR", "Australia": "AUS", "Turkey": "TUR", "Türkiye": "TUR",
    "Germany": "GER", "Curaçao": "CUW", "Ivory Coast": "CIV", "Côte d'Ivoire": "CIV", "Ecuador": "ECU",
    "Netherlands": "NED", "Japan": "JPN", "Sweden": "SWE", "Tunisia": "TUN",
    "Belgium": "BEL", "Egypt": "EGY", "Iran": "IRN", "New Zealand": "NZL",
    "Spain": "ESP", "Cape Verde": "CPV", "Saudi Arabia": "KSA", "Uruguay": "URU",
    "France": "FRA", "Senegal": "SEN", "Iraq": "IRQ", "Norway": "NOR",
    "Argentina": "ARG", "Algeria": "ALG", "Austria": "AUT", "Jordan": "JOR",
    "Portugal": "POR", "DR Congo": "COD", "Uzbekistan": "UZB", "Colombia": "COL",
    "England": "ENG", "Croatia": "CRO", "Ghana": "GHA", "Panama": "PAN",
}
CODE_TO_NAMES = defaultdict(list)
for n, c in NAME_TO_CODE.items():
    CODE_TO_NAMES[c].append(n)


def main():
    # cargar matches por equipo
    matches_by_team = defaultdict(list)  # name -> list of (date, gf, ga, neutral, tournament)
    with open(RAW, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                date = row["date"]
                h = row["home_team"].strip()
                a = row["away_team"].strip()
                hs = int(row["home_score"])
                as_ = int(row["away_score"])
                neutral = row.get("neutral", "False").strip().lower() == "true"
                tournament = row.get("tournament", "Friendly")
                matches_by_team[h].append((date, hs, as_, neutral, tournament, "home"))
                matches_by_team[a].append((date, as_, hs, neutral, tournament, "away"))
            except Exception:
                continue

    # ordenar cronológicamente
    for k in matches_by_team:
        matches_by_team[k].sort(key=lambda x: x[0])

    teams = json.loads((OUT / "teams.json").read_text(encoding="utf-8"))
    features = {}
    today = datetime(2026, 5, 21).date()

    for t in teams:
        code = t["code"]
        names = CODE_TO_NAMES.get(code, [])
        all_matches = []
        for n in names:
            all_matches.extend(matches_by_team.get(n, []))
        all_matches.sort(key=lambda x: x[0])

        if not all_matches:
            continue

        # Últimos 10 partidos (form)
        recent = all_matches[-10:]
        gd_recent = sum(m[1] - m[2] for m in recent)
        gf_recent = sum(m[1] for m in recent)
        ga_recent = sum(m[2] for m in recent)
        avg_gf = gf_recent / max(len(recent), 1)
        avg_ga = ga_recent / max(len(recent), 1)
        wins_recent = sum(1 for m in recent if m[1] > m[2])
        draws_recent = sum(1 for m in recent if m[1] == m[2])

        # WC histórico
        wc_matches = [m for m in all_matches if "FIFA World Cup" in m[4]]
        wc_wins = sum(1 for m in wc_matches if m[1] > m[2])
        wc_total = len(wc_matches)
        wc_winrate = wc_wins / wc_total if wc_total > 0 else 0.0

        # Últimos 365 días
        last_year = [m for m in all_matches if _date(m[0]) >= today - timedelta(days=365)]
        gd_year = sum(m[1] - m[2] for m in last_year)
        n_year = len(last_year)

        features[code] = {
            "n_total_matches": len(all_matches),
            "form_gd_last10": gd_recent,
            "form_wins_last10": wins_recent,
            "form_draws_last10": draws_recent,
            "form_avg_gf_last10": round(avg_gf, 2),
            "form_avg_ga_last10": round(avg_ga, 2),
            "wc_matches_all_time": wc_total,
            "wc_winrate": round(wc_winrate, 3),
            "n_matches_last_365d": n_year,
            "gd_last_365d": gd_year,
        }

    (OUT / "team_features.json").write_text(
        json.dumps(features, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"✓ team_features.json: {len(features)} equipos con form features")

    # Mostrar muestra
    sample_codes = ["ARG", "ESP", "FRA", "BRA", "MEX", "USA", "MAR", "COL", "JOR"]
    print(f"\n{'Code':<5} {'Match':<6} {'GD-10':>5} {'W-10':>4} {'D-10':>4} {'WC%':>5} {'GD-1y':>6}")
    for code in sample_codes:
        f = features.get(code)
        if f:
            print(f"{code:<5} {f['n_total_matches']:<6} {f['form_gd_last10']:>+5d} "
                  f"{f['form_wins_last10']:>4} {f['form_draws_last10']:>4} "
                  f"{f['wc_winrate']*100:>4.0f}% {f['gd_last_365d']:>+6d}")


def _date(s):
    return datetime.strptime(s, "%Y-%m-%d").date() if len(s) >= 10 else datetime(1900, 1, 1).date()


if __name__ == "__main__":
    main()
