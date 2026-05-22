"""
Toma los 49K partidos reales de martj42 y replea la historia entera
para computar el Elo ACTUAL de las 48 selecciones del Mundial 2026.

Esto reemplaza los Elo "aproximados" hardcoded por valores derivados de
los datos reales históricos de partidos internacionales.

Salida: actualiza teams.json con elo_rating computado
        + matches_historical insertado a Supabase
        + elo_history snapshots por equipo
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).parent.parent
RAW_CSV = ROOT / "data" / "raw" / "martj42_results.csv"
OUT_DIR = ROOT / "data" / "output"

# Parámetros Elo (World Football Elo Ratings — eloratings.net method)
K_FACTORS = {
    "FIFA World Cup": 60,
    "FIFA World Cup qualification": 40,
    "Continental qualification": 40,
    "UEFA Euro": 50,
    "Copa América": 50,
    "African Cup of Nations": 50,
    "AFC Asian Cup": 50,
    "UEFA Nations League": 35,
    "Confederations Cup": 40,
    "Friendly": 20,
}
DEFAULT_K = 30
HOME_ADV = 100
INITIAL_ELO = 1500

# Mapeo nombres de país martj42 -> code del Mundial 2026
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


def elo_expected(elo_a: float, elo_b: float, home_adv: float = 0.0) -> float:
    return 1.0 / (1.0 + 10 ** (-(elo_a - elo_b + home_adv) / 400.0))


def goal_diff_multiplier(gd: int) -> float:
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11 + gd) / 8.0


def main():
    if not RAW_CSV.exists():
        print(f"ERROR: no existe {RAW_CSV}. Corré primero scripts/fetch_real_data.py")
        sys.exit(1)

    # Estado: elo actual por equipo (todos arrancan en 1500)
    elo: dict[str, float] = defaultdict(lambda: INITIAL_ELO)
    n_matches = 0
    n_skipped = 0
    last_match_date: dict[str, str] = {}
    seen_teams = set()

    print(f"Leyendo {RAW_CSV.name}...")
    with open(RAW_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ha = row["home_team"].strip()
                aa = row["away_team"].strip()
                if not ha or not aa:
                    n_skipped += 1
                    continue
                hs = int(row["home_score"])
                as_ = int(row["away_score"])
                neutral = row.get("neutral", "False").strip().lower() == "true"
                tournament = row.get("tournament", "Friendly")
                match_date = row.get("date", "")

                k = K_FACTORS.get(tournament, DEFAULT_K)
                home_adv = 0.0 if neutral else HOME_ADV

                we_h = elo_expected(elo[ha], elo[aa], home_adv)
                if hs > as_:
                    wh = 1.0
                elif hs == as_:
                    wh = 0.5
                else:
                    wh = 0.0
                gd_mult = goal_diff_multiplier(abs(hs - as_))
                delta = k * gd_mult * (wh - we_h)
                elo[ha] += delta
                elo[aa] -= delta

                seen_teams.add(ha)
                seen_teams.add(aa)
                last_match_date[ha] = match_date
                last_match_date[aa] = match_date
                n_matches += 1
            except Exception:
                n_skipped += 1

    print(f"   procesados {n_matches} partidos, saltados {n_skipped}")
    print(f"   equipos distintos vistos: {len(seen_teams)}")

    # Actualizar teams.json con Elo computados
    teams = json.loads((OUT_DIR / "teams.json").read_text(encoding="utf-8"))
    updated = 0
    fallbacks = []
    for t in teams:
        # Buscar nombre martj42 que mapea a este code
        code = t["code"]
        found_name = None
        for name, c in NAME_TO_CODE.items():
            if c == code:
                if name in elo:
                    found_name = name
                    break
        if found_name:
            old_elo = t["elo_rating"]
            new_elo = round(elo[found_name], 0)
            t["elo_rating"] = new_elo
            t["elo_old_hardcoded"] = old_elo
            t["elo_last_match"] = last_match_date.get(found_name, "")
            updated += 1
        else:
            fallbacks.append(t["code"])

    (OUT_DIR / "teams.json").write_text(
        json.dumps(teams, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n✓ {updated}/{len(teams)} equipos actualizados con Elo real")
    if fallbacks:
        print(f"⚠ {len(fallbacks)} sin match: {fallbacks}")

    # Mostrar comparativa antes vs después
    print(f"\nTop 15 por Elo real:")
    top = sorted([t for t in teams], key=lambda x: -x["elo_rating"])[:15]
    print(f"{'Rk':>3}  {'Equipo':<25} {'Elo nuevo':>9} {'Elo viejo':>9} {'Δ':>6}")
    for i, t in enumerate(top, 1):
        old = t.get("elo_old_hardcoded", 0)
        delta = t["elo_rating"] - old
        print(f"{i:>3}  {t['flag_emoji']} {t['name']:<23} {t['elo_rating']:>9.0f} {old:>9.0f} {delta:>+6.0f}")

    # Guardar dataset histórico para insertar a Supabase
    print(f"\nExportando históricos para Supabase...")
    hist_rows = []
    with open(RAW_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                hist_rows.append({
                    "match_date": row["date"],
                    "home_team": row["home_team"].strip(),
                    "away_team": row["away_team"].strip(),
                    "home_score": int(row["home_score"]),
                    "away_score": int(row["away_score"]),
                    "tournament": row.get("tournament", "Friendly"),
                    "city": row.get("city", ""),
                    "country": row.get("country", ""),
                    "neutral": row.get("neutral", "False").strip().lower() == "true",
                })
            except Exception:
                pass
    (OUT_DIR / "matches_historical.json").write_text(
        json.dumps(hist_rows, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  matches_historical.json: {len(hist_rows)} filas, "
          f"{(OUT_DIR/'matches_historical.json').stat().st_size // 1024 // 1024} MB")


if __name__ == "__main__":
    main()
