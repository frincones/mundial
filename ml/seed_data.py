"""
Genera la data semilla del Mundial 2026:
- 48 equipos con grupos (segun sorteo oficial 5 dic 2025)
- Elo ratings iniciales (basado en eloratings.net abr 2026 + FIFA ranking)
- 104 partidos del fixture (fase de grupos + eliminatoria)

Salida: data/output/teams.json + matches.json
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

# =============================================================================
# 48 EQUIPOS POR GRUPO (sorteo oficial WC2026 — 5 dic 2025 Washington DC)
# Elo ratings aproximados de eloratings.net + FIFA ranking abril 2026
# =============================================================================
TEAMS = [
    # GRUPO A — Estadio Azteca, México
    {"code": "MEX", "name": "México",        "flag": "🇲🇽", "conf": "CONCACAF", "group": "A", "seed": 1, "host": True,  "elo": 1820, "fifa_rank": 19, "manager": "Javier Aguirre"},
    {"code": "RSA", "name": "Sudáfrica",     "flag": "🇿🇦", "conf": "CAF",     "group": "A", "seed": 4, "host": False, "elo": 1755, "fifa_rank": 53, "manager": "Hugo Broos"},
    {"code": "KOR", "name": "Corea del Sur", "flag": "🇰🇷", "conf": "AFC",     "group": "A", "seed": 3, "host": False, "elo": 1796, "fifa_rank": 23, "manager": "Hong Myung-bo"},
    {"code": "CZE", "name": "República Checa","flag": "🇨🇿","conf": "UEFA",    "group": "A", "seed": 2, "host": False, "elo": 1788, "fifa_rank": 34, "manager": "Ivan Hašek"},

    # GRUPO B — Canadá
    {"code": "CAN", "name": "Canadá",        "flag": "🇨🇦", "conf": "CONCACAF","group": "B", "seed": 1, "host": True,  "elo": 1755, "fifa_rank": 30, "manager": "Jesse Marsch"},
    {"code": "BIH", "name": "Bosnia",        "flag": "🇧🇦", "conf": "UEFA",    "group": "B", "seed": 4, "host": False, "elo": 1690, "fifa_rank": 64, "manager": "Sergej Barbarez"},
    {"code": "QAT", "name": "Qatar",         "flag": "🇶🇦", "conf": "AFC",     "group": "B", "seed": 3, "host": False, "elo": 1680, "fifa_rank": 56, "manager": "Tintín Márquez"},
    {"code": "SUI", "name": "Suiza",         "flag": "🇨🇭", "conf": "UEFA",    "group": "B", "seed": 2, "host": False, "elo": 1830, "fifa_rank": 17, "manager": "Murat Yakın"},

    # GRUPO C
    {"code": "BRA", "name": "Brasil",        "flag": "🇧🇷", "conf": "CONMEBOL","group": "C", "seed": 1, "host": False, "elo": 1995, "fifa_rank": 5,  "manager": "Carlo Ancelotti"},
    {"code": "MAR", "name": "Marruecos",     "flag": "🇲🇦", "conf": "CAF",     "group": "C", "seed": 2, "host": False, "elo": 1855, "fifa_rank": 14, "manager": "Walid Regragui"},
    {"code": "HAI", "name": "Haití",         "flag": "🇭🇹", "conf": "CONCACAF","group": "C", "seed": 4, "host": False, "elo": 1565, "fifa_rank": 85, "manager": "Sébastien Migné"},
    {"code": "SCO", "name": "Escocia",       "flag": "🏴", "conf": "UEFA",    "group": "C", "seed": 3, "host": False, "elo": 1795, "fifa_rank": 38, "manager": "Steve Clarke"},

    # GRUPO D
    {"code": "USA", "name": "Estados Unidos","flag": "🇺🇸", "conf": "CONCACAF","group": "D", "seed": 1, "host": True,  "elo": 1815, "fifa_rank": 16, "manager": "Mauricio Pochettino"},
    {"code": "PAR", "name": "Paraguay",      "flag": "🇵🇾", "conf": "CONMEBOL","group": "D", "seed": 3, "host": False, "elo": 1780, "fifa_rank": 41, "manager": "Gustavo Alfaro"},
    {"code": "AUS", "name": "Australia",     "flag": "🇦🇺", "conf": "AFC",     "group": "D", "seed": 4, "host": False, "elo": 1735, "fifa_rank": 26, "manager": "Tony Popovic"},
    {"code": "TUR", "name": "Turquía",       "flag": "🇹🇷", "conf": "UEFA",    "group": "D", "seed": 2, "host": False, "elo": 1810, "fifa_rank": 25, "manager": "Vincenzo Montella"},

    # GRUPO E
    {"code": "GER", "name": "Alemania",      "flag": "🇩🇪", "conf": "UEFA",    "group": "E", "seed": 1, "host": False, "elo": 1965, "fifa_rank": 9,  "manager": "Julian Nagelsmann"},
    {"code": "CUW", "name": "Curazao",       "flag": "🇨🇼", "conf": "CONCACAF","group": "E", "seed": 4, "host": False, "elo": 1530, "fifa_rank": 86, "manager": "Dick Advocaat"},
    {"code": "CIV", "name": "Costa de Marfil","flag":"🇨🇮", "conf": "CAF",     "group": "E", "seed": 3, "host": False, "elo": 1755, "fifa_rank": 42, "manager": "Emerse Faé"},
    {"code": "ECU", "name": "Ecuador",       "flag": "🇪🇨", "conf": "CONMEBOL","group": "E", "seed": 2, "host": False, "elo": 1830, "fifa_rank": 22, "manager": "Sebastián Beccacece"},

    # GRUPO F
    {"code": "NED", "name": "Países Bajos",  "flag": "🇳🇱", "conf": "UEFA",    "group": "F", "seed": 1, "host": False, "elo": 1955, "fifa_rank": 7,  "manager": "Ronald Koeman"},
    {"code": "JPN", "name": "Japón",         "flag": "🇯🇵", "conf": "AFC",     "group": "F", "seed": 2, "host": False, "elo": 1850, "fifa_rank": 15, "manager": "Hajime Moriyasu"},
    {"code": "SWE", "name": "Suecia",        "flag": "🇸🇪", "conf": "UEFA",    "group": "F", "seed": 3, "host": False, "elo": 1750, "fifa_rank": 36, "manager": "Graham Potter"},
    {"code": "TUN", "name": "Túnez",         "flag": "🇹🇳", "conf": "CAF",     "group": "F", "seed": 4, "host": False, "elo": 1700, "fifa_rank": 49, "manager": "Sami Trabelsi"},

    # GRUPO G
    {"code": "BEL", "name": "Bélgica",       "flag": "🇧🇪", "conf": "UEFA",    "group": "G", "seed": 1, "host": False, "elo": 1925, "fifa_rank": 8,  "manager": "Rudi Garcia"},
    {"code": "EGY", "name": "Egipto",        "flag": "🇪🇬", "conf": "CAF",     "group": "G", "seed": 2, "host": False, "elo": 1760, "fifa_rank": 35, "manager": "Hossam Hassan"},
    {"code": "IRN", "name": "Irán",          "flag": "🇮🇷", "conf": "AFC",     "group": "G", "seed": 3, "host": False, "elo": 1770, "fifa_rank": 21, "manager": "Amir Ghalenoei"},
    {"code": "NZL", "name": "Nueva Zelanda", "flag": "🇳🇿", "conf": "OFC",     "group": "G", "seed": 4, "host": False, "elo": 1580, "fifa_rank": 89, "manager": "Darren Bazeley"},

    # GRUPO H
    {"code": "ESP", "name": "España",        "flag": "🇪🇸", "conf": "UEFA",    "group": "H", "seed": 1, "host": False, "elo": 2025, "fifa_rank": 3,  "manager": "Luis de la Fuente"},
    {"code": "CPV", "name": "Cabo Verde",    "flag": "🇨🇻", "conf": "CAF",     "group": "H", "seed": 4, "host": False, "elo": 1560, "fifa_rank": 73, "manager": "Bubista"},
    {"code": "KSA", "name": "Arabia Saudita","flag": "🇸🇦", "conf": "AFC",     "group": "H", "seed": 3, "host": False, "elo": 1665, "fifa_rank": 58, "manager": "Hervé Renard"},
    {"code": "URU", "name": "Uruguay",       "flag": "🇺🇾", "conf": "CONMEBOL","group": "H", "seed": 2, "host": False, "elo": 1885, "fifa_rank": 11, "manager": "Marcelo Bielsa"},

    # GRUPO I
    {"code": "FRA", "name": "Francia",       "flag": "🇫🇷", "conf": "UEFA",    "group": "I", "seed": 1, "host": False, "elo": 2030, "fifa_rank": 2,  "manager": "Didier Deschamps"},
    {"code": "SEN", "name": "Senegal",       "flag": "🇸🇳", "conf": "CAF",     "group": "I", "seed": 2, "host": False, "elo": 1815, "fifa_rank": 18, "manager": "Pape Thiaw"},
    {"code": "IRQ", "name": "Irak",          "flag": "🇮🇶", "conf": "AFC",     "group": "I", "seed": 4, "host": False, "elo": 1620, "fifa_rank": 57, "manager": "Graham Arnold"},
    {"code": "NOR", "name": "Noruega",       "flag": "🇳🇴", "conf": "UEFA",    "group": "I", "seed": 3, "host": False, "elo": 1825, "fifa_rank": 33, "manager": "Ståle Solbakken"},

    # GRUPO J — Argentina campeón vigente
    {"code": "ARG", "name": "Argentina",     "flag": "🇦🇷", "conf": "CONMEBOL","group": "J", "seed": 1, "host": False, "elo": 2080, "fifa_rank": 1,  "manager": "Lionel Scaloni"},
    {"code": "ALG", "name": "Argelia",       "flag": "🇩🇿", "conf": "CAF",     "group": "J", "seed": 3, "host": False, "elo": 1730, "fifa_rank": 39, "manager": "Vladimir Petković"},
    {"code": "AUT", "name": "Austria",       "flag": "🇦🇹", "conf": "UEFA",    "group": "J", "seed": 2, "host": False, "elo": 1830, "fifa_rank": 24, "manager": "Ralf Rangnick"},
    {"code": "JOR", "name": "Jordania",      "flag": "🇯🇴", "conf": "AFC",     "group": "J", "seed": 4, "host": False, "elo": 1600, "fifa_rank": 65, "manager": "Jamal Sellami", "debut": True},

    # GRUPO K
    {"code": "POR", "name": "Portugal",      "flag": "🇵🇹", "conf": "UEFA",    "group": "K", "seed": 1, "host": False, "elo": 1985, "fifa_rank": 6,  "manager": "Roberto Martínez"},
    {"code": "COD", "name": "RD Congo",      "flag": "🇨🇩", "conf": "CAF",     "group": "K", "seed": 3, "host": False, "elo": 1690, "fifa_rank": 55, "manager": "Sébastien Desabre"},
    {"code": "UZB", "name": "Uzbekistán",    "flag": "🇺🇿", "conf": "AFC",     "group": "K", "seed": 4, "host": False, "elo": 1655, "fifa_rank": 62, "manager": "Timur Kapadze", "debut": True},
    {"code": "COL", "name": "Colombia",      "flag": "🇨🇴", "conf": "CONMEBOL","group": "K", "seed": 2, "host": False, "elo": 1900, "fifa_rank": 12, "manager": "Néstor Lorenzo"},

    # GRUPO L
    {"code": "ENG", "name": "Inglaterra",    "flag": "🏴", "conf": "UEFA",    "group": "L", "seed": 1, "host": False, "elo": 2000, "fifa_rank": 4,  "manager": "Thomas Tuchel"},
    {"code": "CRO", "name": "Croacia",       "flag": "🇭🇷", "conf": "UEFA",    "group": "L", "seed": 2, "host": False, "elo": 1860, "fifa_rank": 10, "manager": "Zlatko Dalić"},
    {"code": "GHA", "name": "Ghana",         "flag": "🇬🇭", "conf": "CAF",     "group": "L", "seed": 3, "host": False, "elo": 1720, "fifa_rank": 70, "manager": "Otto Addo"},
    {"code": "PAN", "name": "Panamá",        "flag": "🇵🇦", "conf": "CONCACAF","group": "L", "seed": 4, "host": False, "elo": 1665, "fifa_rank": 33, "manager": "Thomas Christiansen"},
]

# =============================================================================
# FIXTURE — 72 partidos de fase de grupos + 32 de eliminatoria = 104 total
# Fechas oficiales WC2026: 11 jun – 19 jul
# =============================================================================
# Apertura 11-jun (MEX vs RSA), final 19-jul

from datetime import date, timedelta

GROUP_DATES = {
    "round1": date(2026, 6, 11),  # Jornada 1: 11-15 jun
    "round2": date(2026, 6, 16),  # Jornada 2: 16-21 jun
    "round3": date(2026, 6, 22),  # Jornada 3: 22-27 jun
}

VENUES = {
    "A": ("Mexico City", "Estadio Azteca", "MEX"),
    "B": ("Toronto", "BMO Field", "CAN"),
    "C": ("Atlanta", "Mercedes-Benz Stadium", "USA"),
    "D": ("Los Angeles", "SoFi Stadium", "USA"),
    "E": ("Dallas", "AT&T Stadium", "USA"),
    "F": ("Houston", "NRG Stadium", "USA"),
    "G": ("Boston", "Gillette Stadium", "USA"),
    "H": ("Miami", "Hard Rock Stadium", "USA"),
    "I": ("Philadelphia", "Lincoln Financial Field", "USA"),
    "J": ("Vancouver", "BC Place", "CAN"),
    "K": ("Guadalajara", "Estadio Akron", "MEX"),
    "L": ("Seattle", "Lumen Field", "USA"),
}

# Knockout venues
KNOCKOUT_VENUES = {
    "r32": [
        ("New York", "MetLife Stadium", "USA"),
        ("Kansas City", "GEHA Field at Arrowhead", "USA"),
        ("Monterrey", "Estadio BBVA", "MEX"),
        ("San Francisco", "Levi's Stadium", "USA"),
    ],
    "r16": [
        ("Atlanta", "Mercedes-Benz Stadium", "USA"),
        ("Boston", "Gillette Stadium", "USA"),
        ("Dallas", "AT&T Stadium", "USA"),
        ("Los Angeles", "SoFi Stadium", "USA"),
    ],
    "qf": [
        ("Boston", "Gillette Stadium", "USA"),
        ("Los Angeles", "SoFi Stadium", "USA"),
        ("Miami", "Hard Rock Stadium", "USA"),
        ("Kansas City", "GEHA Field at Arrowhead", "USA"),
    ],
    "sf": [
        ("Dallas", "AT&T Stadium", "USA"),
        ("Atlanta", "Mercedes-Benz Stadium", "USA"),
    ],
    "3rd": [("Miami", "Hard Rock Stadium", "USA")],
    "final": [("East Rutherford", "MetLife Stadium", "USA")],
}


def build_group_matches():
    """72 partidos de fase de grupos (cada grupo de 4 juega 6 partidos: 1v2, 1v3, 1v4, 2v3, 2v4, 3v4)."""
    matches = []
    match_n = 1
    pairings = [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]  # 6 pairings per group

    # Distribuir las 6 jornadas del grupo en 3 fechas (2 partidos por jornada)
    # Match 1 (1v2 + 3v4) -> day 0
    # Match 2 (1v3 + 2v4) -> day 5
    # Match 3 (1v4 + 2v3) -> day 11

    groups = sorted(set(t["group"] for t in TEAMS))
    base_date = date(2026, 6, 11)

    for g_idx, g in enumerate(groups):
        teams_g = sorted([t for t in TEAMS if t["group"] == g], key=lambda x: x["seed"])
        venue = VENUES[g]
        for pair_idx, (i, j) in enumerate(pairings):
            # 6 partidos por grupo, distribuir en 3 jornadas
            jornada = pair_idx // 2  # 0, 0, 1, 1, 2, 2
            offset_days = {0: 0, 1: 5, 2: 11}[jornada]
            # spread groups across days within each jornada
            match_date = base_date + timedelta(days=offset_days + (g_idx % 5))
            scheduled = datetime.combine(match_date, datetime.min.time(), tzinfo=timezone.utc)
            scheduled = scheduled.replace(hour=18 + (pair_idx % 2) * 3)

            matches.append({
                "match_number": match_n,
                "stage": "group",
                "group_letter": g,
                "scheduled_at": scheduled.isoformat(),
                "venue_city": venue[0],
                "venue_stadium": venue[1],
                "venue_country": venue[2],
                "home_team_code": teams_g[i]["code"],
                "away_team_code": teams_g[j]["code"],
                "home_label": None,
                "away_label": None,
                "home_score": None,
                "away_score": None,
                "status": "scheduled",
            })
            match_n += 1

    return matches


def build_knockout_matches():
    """32 partidos: R32 (16) + R16 (8) + QF (4) + SF (2) + 3rd (1) + Final (1) = 32."""
    matches = []
    match_n = 73  # after group stage

    # Round of 32 (16 matches) — 28 jun a 3 jul
    r32_start = date(2026, 6, 28)
    for i in range(16):
        scheduled = datetime.combine(r32_start + timedelta(days=i // 4), datetime.min.time(), tzinfo=timezone.utc)
        hour_options = [15, 18, 21, 12]
        scheduled = scheduled.replace(hour=hour_options[i % 4])
        v = KNOCKOUT_VENUES["r32"][i % 4]
        matches.append({
            "match_number": match_n, "stage": "r32", "group_letter": None,
            "scheduled_at": scheduled.isoformat(),
            "venue_city": v[0], "venue_stadium": v[1], "venue_country": v[2],
            "home_team_code": None, "away_team_code": None,
            "home_label": f"R32-{i+1} (TBD)", "away_label": f"R32-{i+1} (TBD)",
            "home_score": None, "away_score": None, "status": "scheduled",
        })
        match_n += 1

    # Round of 16 (8 matches) — 4-7 jul
    r16_start = date(2026, 7, 4)
    for i in range(8):
        scheduled = datetime.combine(r16_start + timedelta(days=i // 2), datetime.min.time(), tzinfo=timezone.utc)
        scheduled = scheduled.replace(hour=15 + (i % 2) * 4)
        v = KNOCKOUT_VENUES["r16"][i % 4]
        matches.append({
            "match_number": match_n, "stage": "r16", "group_letter": None,
            "scheduled_at": scheduled.isoformat(),
            "venue_city": v[0], "venue_stadium": v[1], "venue_country": v[2],
            "home_team_code": None, "away_team_code": None,
            "home_label": f"R16-{i+1} (TBD)", "away_label": f"R16-{i+1} (TBD)",
            "home_score": None, "away_score": None, "status": "scheduled",
        })
        match_n += 1

    # Quarterfinals (4 matches) — 9-11 jul
    qf_dates = [date(2026, 7, 9), date(2026, 7, 10), date(2026, 7, 11), date(2026, 7, 11)]
    for i in range(4):
        scheduled = datetime.combine(qf_dates[i], datetime.min.time(), tzinfo=timezone.utc).replace(hour=17)
        v = KNOCKOUT_VENUES["qf"][i]
        matches.append({
            "match_number": match_n, "stage": "qf", "group_letter": None,
            "scheduled_at": scheduled.isoformat(),
            "venue_city": v[0], "venue_stadium": v[1], "venue_country": v[2],
            "home_team_code": None, "away_team_code": None,
            "home_label": f"QF-{i+1} (TBD)", "away_label": f"QF-{i+1} (TBD)",
            "home_score": None, "away_score": None, "status": "scheduled",
        })
        match_n += 1

    # Semifinals (2 matches) — 14, 15 jul
    sf_dates = [date(2026, 7, 14), date(2026, 7, 15)]
    for i in range(2):
        scheduled = datetime.combine(sf_dates[i], datetime.min.time(), tzinfo=timezone.utc).replace(hour=20)
        v = KNOCKOUT_VENUES["sf"][i]
        matches.append({
            "match_number": match_n, "stage": "sf", "group_letter": None,
            "scheduled_at": scheduled.isoformat(),
            "venue_city": v[0], "venue_stadium": v[1], "venue_country": v[2],
            "home_team_code": None, "away_team_code": None,
            "home_label": f"SF-{i+1} (TBD)", "away_label": f"SF-{i+1} (TBD)",
            "home_score": None, "away_score": None, "status": "scheduled",
        })
        match_n += 1

    # 3rd place — 18 jul
    v = KNOCKOUT_VENUES["3rd"][0]
    scheduled = datetime(2026, 7, 18, 16, 0, tzinfo=timezone.utc)
    matches.append({
        "match_number": match_n, "stage": "3rd", "group_letter": None,
        "scheduled_at": scheduled.isoformat(),
        "venue_city": v[0], "venue_stadium": v[1], "venue_country": v[2],
        "home_team_code": None, "away_team_code": None,
        "home_label": "Loser SF1", "away_label": "Loser SF2",
        "home_score": None, "away_score": None, "status": "scheduled",
    })
    match_n += 1

    # Final — 19 jul
    v = KNOCKOUT_VENUES["final"][0]
    scheduled = datetime(2026, 7, 19, 19, 0, tzinfo=timezone.utc)
    matches.append({
        "match_number": match_n, "stage": "final", "group_letter": None,
        "scheduled_at": scheduled.isoformat(),
        "venue_city": v[0], "venue_stadium": v[1], "venue_country": v[2],
        "home_team_code": None, "away_team_code": None,
        "home_label": "Winner SF1", "away_label": "Winner SF2",
        "home_score": None, "away_score": None, "status": "scheduled",
    })

    return matches


def main():
    out_dir = Path(__file__).parent.parent / "data" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Teams
    teams_data = []
    for t in TEAMS:
        teams_data.append({
            "code": t["code"],
            "name": t["name"],
            "flag_emoji": t["flag"],
            "confederation": t["conf"],
            "group_letter": t["group"],
            "group_position": t["seed"],
            "is_host": t.get("host", False),
            "fifa_rank": t.get("fifa_rank"),
            "elo_rating": t["elo"],
            "manager_name": t.get("manager"),
            "is_debut": t.get("debut", False),
        })
    (out_dir / "teams.json").write_text(json.dumps(teams_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ teams.json: {len(teams_data)} equipos")

    # Matches
    group_matches = build_group_matches()
    knockout_matches = build_knockout_matches()
    all_matches = group_matches + knockout_matches
    (out_dir / "matches.json").write_text(json.dumps(all_matches, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ matches.json: {len(all_matches)} partidos ({len(group_matches)} grupo + {len(knockout_matches)} eliminatoria)")

    # Resumen
    print(f"\nResumen:")
    print(f"  48 equipos en 12 grupos (A-L)")
    print(f"  72 partidos fase de grupos")
    print(f"  32 partidos eliminatoria (16 R32 + 8 R16 + 4 QF + 2 SF + 1 3er + 1 Final)")
    print(f"  Total: 104 partidos")


if __name__ == "__main__":
    main()
