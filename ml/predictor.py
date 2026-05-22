"""
Modelo predictivo Mundial 2026:
- Elo update tras cada partido (K=60 mundial)
- Bivariate Poisson para predecir scoreline + probabilidades W/D/L
- Monte Carlo simulator del torneo completo (fase grupos + eliminatoria)

Salidas:
- data/output/predictions.json  (104 partidos con probs + scoreline esperado)
- data/output/simulations.json  (P(campeon) + P(fase X) por equipo)
"""
from __future__ import annotations
import json
import random
import math
from pathlib import Path
from collections import defaultdict
from copy import deepcopy

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"

# =============================================================================
# CONSTANTES DEL MODELO
# =============================================================================
HOME_ADV = 100        # ventaja localía (Elo points) — solo para anfitriones reales
NEUTRAL = True        # mayoría de partidos del Mundial son en sede neutral
K_GROUP = 60          # K-factor para Elo en partidos del Mundial
K_KNOCKOUT = 75       # K-factor mayor en eliminatorias (mayor importancia)
AVG_GOALS_PER_MATCH = 2.55  # promedio histórico Mundiales

MC_SIMULATIONS = 10000  # Monte Carlo
RANDOM_SEED = 42

random.seed(RANDOM_SEED)


# =============================================================================
# ELO PROBABILITY
# =============================================================================
def elo_win_probability(elo_a: float, elo_b: float, home_advantage: float = 0.0) -> float:
    """P(equipo A gana o empata con ventaja a su favor) usando fórmula Elo."""
    diff = elo_a - elo_b + home_advantage
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))


def expected_goals(elo_a: float, elo_b: float, home_advantage: float = 0.0) -> tuple[float, float]:
    """Goles esperados por equipo basados en diferencia Elo.
    Modelo: relaciona la P_win con expected goals via funcion lineal-log."""
    p_a = elo_win_probability(elo_a, elo_b, home_advantage)
    # mapping: p_a=0.5 -> 1.275 goles c/u; p_a=0.7 -> 1.65 vs 0.9; p_a=0.9 -> 2.3 vs 0.4
    # ajuste empirico para que sume ~2.55 goles por partido
    lam_a = AVG_GOALS_PER_MATCH * (0.3 + 0.7 * (2 * p_a)) / 2.0
    lam_b = AVG_GOALS_PER_MATCH * (0.3 + 0.7 * (2 * (1 - p_a))) / 2.0
    return lam_a, lam_b


def poisson_match_outcome(lam_a: float, lam_b: float, max_goals: int = 8) -> dict:
    """Calcula P(home win), P(draw), P(away win) usando Poisson independiente."""
    p_a_win = 0.0
    p_draw = 0.0
    p_b_win = 0.0
    expected_scoreline = (0, 0)
    max_prob = 0.0
    for ga in range(max_goals + 1):
        for gb in range(max_goals + 1):
            p = poisson_pmf(ga, lam_a) * poisson_pmf(gb, lam_b)
            if p > max_prob:
                max_prob = p
                expected_scoreline = (ga, gb)
            if ga > gb:
                p_a_win += p
            elif ga == gb:
                p_draw += p
            else:
                p_b_win += p
    return {
        "prob_home_win": p_a_win,
        "prob_draw": p_draw,
        "prob_away_win": p_b_win,
        "expected_scoreline": expected_scoreline,
        "expected_home_goals": lam_a,
        "expected_away_goals": lam_b,
    }


def poisson_pmf(k: int, lam: float) -> float:
    """P(X=k) para X ~ Poisson(lam)."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def simulate_match_goals(lam_a: float, lam_b: float, rng: random.Random) -> tuple[int, int]:
    """Simula UN resultado de goles según Poisson."""
    return rng.choices(range(15), weights=[poisson_pmf(k, lam_a) for k in range(15)])[0], \
           rng.choices(range(15), weights=[poisson_pmf(k, lam_b) for k in range(15)])[0]


def update_elo(elo_a: float, elo_b: float, ga: int, gb: int, k: float = K_GROUP, home_adv: float = 0.0) -> tuple[float, float]:
    """Update Elo ratings tras un partido (clasic World Football Elo)."""
    # Win expectation
    we_a = elo_win_probability(elo_a, elo_b, home_adv)
    we_b = 1 - we_a

    # Result: A win=1, draw=0.5, A loss=0
    if ga > gb:
        wa = 1.0
    elif ga == gb:
        wa = 0.5
    else:
        wa = 0.0
    wb = 1 - wa

    # Goal difference multiplier (Elo Ratings.net method)
    gd = abs(ga - gb)
    if gd == 0 or gd == 1:
        g_mult = 1.0
    elif gd == 2:
        g_mult = 1.5
    else:
        g_mult = (11 + gd) / 8.0

    new_a = elo_a + k * g_mult * (wa - we_a)
    new_b = elo_b + k * g_mult * (wb - we_b)
    return new_a, new_b


# =============================================================================
# 1) Predict for all 104 matches (group stage only — knockouts depend on group results)
# =============================================================================
def predict_group_stage(teams_by_code: dict, matches: list) -> list:
    """Genera predicciones para los 72 partidos de fase de grupos."""
    predictions = []
    for m in matches:
        if m["stage"] != "group":
            continue
        ta = teams_by_code[m["home_team_code"]]
        tb = teams_by_code[m["away_team_code"]]

        # Determinar ventaja de localía
        home_adv = HOME_ADV if ta.get("is_host") and m["venue_country"] == _country_for_host(ta["code"]) else 0

        lam_a, lam_b = expected_goals(ta["elo_rating"], tb["elo_rating"], home_adv)
        outcome = poisson_match_outcome(lam_a, lam_b)

        # Razones
        elo_diff = ta["elo_rating"] - tb["elo_rating"]
        reasons = []
        if abs(elo_diff) > 50:
            stronger = ta if elo_diff > 0 else tb
            reasons.append({
                "feature": "elo_diff",
                "value": elo_diff,
                "contribution": elo_diff / 100,
                "label": f"{stronger['name']} es Elo {int(abs(elo_diff))} puntos más alto",
            })
        if home_adv > 0:
            reasons.append({
                "feature": "home_advantage",
                "value": home_adv,
                "contribution": home_adv / 100,
                "label": f"{ta['name']} juega de local en su país",
            })

        gh, gv = outcome["expected_scoreline"]
        predicted_winner = (
            ta["code"] if outcome["prob_home_win"] > outcome["prob_away_win"] and outcome["prob_home_win"] > outcome["prob_draw"]
            else tb["code"] if outcome["prob_away_win"] > outcome["prob_draw"]
            else None
        )

        predictions.append({
            "match_number": m["match_number"],
            "stage": m["stage"],
            "home_team_code": m["home_team_code"],
            "away_team_code": m["away_team_code"],
            "prob_home_win": round(outcome["prob_home_win"], 4),
            "prob_draw": round(outcome["prob_draw"], 4),
            "prob_away_win": round(outcome["prob_away_win"], 4),
            "expected_home_goals": round(outcome["expected_home_goals"], 2),
            "expected_away_goals": round(outcome["expected_away_goals"], 2),
            "predicted_winner_code": predicted_winner,
            "predicted_scoreline": f"{gh}-{gv}",
            "reasons": reasons,
        })
    return predictions


def _country_for_host(code: str) -> str:
    return {"USA": "USA", "MEX": "MEX", "CAN": "CAN"}.get(code, "USA")


# =============================================================================
# 2) Monte Carlo simulator del torneo completo
# =============================================================================
def simulate_tournament(teams: list, group_matches: list, n_sims: int = MC_SIMULATIONS) -> dict:
    """
    Simula el torneo completo n_sims veces.
    Devuelve probabilidades de cada equipo de:
    - Ganar el grupo / 2do / 3ro / eliminado
    - Pasar a R16, QF, SF, final, ganar
    """
    by_code = {t["code"]: t for t in teams}

    counts = defaultdict(lambda: {
        "winner": 0, "finalist": 0, "semifinal": 0, "quarterfinal": 0,
        "round_of_16": 0, "round_of_32": 0,
        "group_first": 0, "group_second": 0, "group_third": 0, "eliminated_group": 0,
        "goals_scored": 0, "goals_conceded": 0,
    })

    rng = random.Random(RANDOM_SEED)

    for sim in range(n_sims):
        # Copy Elo ratings (will update during sim)
        elos = {t["code"]: t["elo_rating"] for t in teams}

        # 1. Group stage
        groups = defaultdict(list)  # group_letter -> [(code, pts, gd, gf), ...]
        for t in teams:
            groups[t["group_letter"]].append({"code": t["code"], "pts": 0, "gd": 0, "gf": 0, "ga": 0})

        for m in group_matches:
            if m["stage"] != "group":
                continue
            tc_a, tc_b = m["home_team_code"], m["away_team_code"]
            ta = by_code[tc_a]
            home_adv = HOME_ADV if ta.get("is_host") and m["venue_country"] == _country_for_host(tc_a) else 0
            lam_a, lam_b = expected_goals(elos[tc_a], elos[tc_b], home_adv)
            ga, gb = simulate_match_goals(lam_a, lam_b, rng)
            # Update Elo
            elos[tc_a], elos[tc_b] = update_elo(elos[tc_a], elos[tc_b], ga, gb, K_GROUP, home_adv)
            # Update standings
            g = m["group_letter"]
            row_a = next(r for r in groups[g] if r["code"] == tc_a)
            row_b = next(r for r in groups[g] if r["code"] == tc_b)
            row_a["gf"] += ga; row_a["ga"] += gb; row_a["gd"] += ga - gb
            row_b["gf"] += gb; row_b["ga"] += ga; row_b["gd"] += gb - ga
            if ga > gb:
                row_a["pts"] += 3
            elif ga == gb:
                row_a["pts"] += 1; row_b["pts"] += 1
            else:
                row_b["pts"] += 3
            # tracking stats
            counts[tc_a]["goals_scored"] += ga
            counts[tc_a]["goals_conceded"] += gb
            counts[tc_b]["goals_scored"] += gb
            counts[tc_b]["goals_conceded"] += ga

        # 2. Determinar 32 clasificados (2 primeros + 8 mejores 3ros)
        qualified = []
        thirds = []
        for letter, rows in groups.items():
            rows.sort(key=lambda r: (-r["pts"], -r["gd"], -r["gf"]))
            counts[rows[0]["code"]]["group_first"] += 1
            counts[rows[1]["code"]]["group_second"] += 1
            counts[rows[2]["code"]]["group_third"] += 1
            counts[rows[3]["code"]]["eliminated_group"] += 1
            qualified.append({"code": rows[0]["code"], "rank": 1, "group": letter, "pts": rows[0]["pts"], "gd": rows[0]["gd"], "gf": rows[0]["gf"]})
            qualified.append({"code": rows[1]["code"], "rank": 2, "group": letter, "pts": rows[1]["pts"], "gd": rows[1]["gd"], "gf": rows[1]["gf"]})
            thirds.append({"code": rows[2]["code"], "rank": 3, "group": letter, "pts": rows[2]["pts"], "gd": rows[2]["gd"], "gf": rows[2]["gf"]})

        # 8 mejores terceros
        thirds.sort(key=lambda r: (-r["pts"], -r["gd"], -r["gf"]))
        qualified.extend(thirds[:8])

        # 3. R32 — emparejamientos sencillos (en la realidad hay seeding complejo,
        # acá emparejamos por ranking simple para una buena aproximación)
        qualified.sort(key=lambda r: (-r["pts"] * 10 - r["gd"] - elos[r["code"]] / 100))
        # 32 equipos: emparejar 1 vs 32, 2 vs 31, etc
        r32 = list(zip(qualified[:16], qualified[16:][::-1]))

        # tracking R32
        for q in qualified:
            counts[q["code"]]["round_of_32"] += 1

        # Helper: knockout match
        def play_knockout(team_a_code, team_b_code, k=K_KNOCKOUT):
            lam_a, lam_b = expected_goals(elos[team_a_code], elos[team_b_code])
            ga, gb = simulate_match_goals(lam_a, lam_b, rng)
            counts[team_a_code]["goals_scored"] += ga
            counts[team_a_code]["goals_conceded"] += gb
            counts[team_b_code]["goals_scored"] += gb
            counts[team_b_code]["goals_conceded"] += ga
            if ga == gb:
                # penal: elige por Elo + ruido
                p_a = elo_win_probability(elos[team_a_code], elos[team_b_code]) * 0.6 + 0.2 + rng.uniform(0, 0.2)
                winner = team_a_code if rng.random() < p_a else team_b_code
            else:
                winner = team_a_code if ga > gb else team_b_code
            elos[team_a_code], elos[team_b_code] = update_elo(elos[team_a_code], elos[team_b_code], ga, gb, k)
            return winner

        # R32 -> R16 (16 winners)
        r16_winners = []
        for a, b in r32:
            w = play_knockout(a["code"], b["code"])
            r16_winners.append(w)
            counts[w]["round_of_16"] += 1

        # R16 -> QF (8 winners)
        qf_winners = []
        for i in range(0, 16, 2):
            w = play_knockout(r16_winners[i], r16_winners[i+1])
            qf_winners.append(w)
            counts[w]["quarterfinal"] += 1

        # QF -> SF (4 winners)
        sf_winners = []
        for i in range(0, 8, 2):
            w = play_knockout(qf_winners[i], qf_winners[i+1])
            sf_winners.append(w)
            counts[w]["semifinal"] += 1

        # SF -> Final (2 winners)
        finalists = []
        for i in range(0, 4, 2):
            w = play_knockout(sf_winners[i], sf_winners[i+1])
            finalists.append(w)
            counts[w]["finalist"] += 1

        # Final
        champion = play_knockout(finalists[0], finalists[1])
        counts[champion]["winner"] += 1

    # Normalizar a probabilidades
    results = []
    for code, c in counts.items():
        results.append({
            "team_code": code,
            "n_simulations": n_sims,
            "prob_winner":          c["winner"] / n_sims,
            "prob_finalist":        c["finalist"] / n_sims,
            "prob_semifinal":       c["semifinal"] / n_sims,
            "prob_quarterfinal":    c["quarterfinal"] / n_sims,
            "prob_round_of_16":     c["round_of_16"] / n_sims,
            "prob_round_of_32":     c["round_of_32"] / n_sims,
            "prob_group_first":     c["group_first"] / n_sims,
            "prob_group_second":    c["group_second"] / n_sims,
            "prob_group_third":     c["group_third"] / n_sims,
            "prob_eliminated_group": c["eliminated_group"] / n_sims,
            "avg_goals_scored":     c["goals_scored"] / n_sims,
            "avg_goals_conceded":   c["goals_conceded"] / n_sims,
        })
    return sorted(results, key=lambda r: -r["prob_winner"])


# =============================================================================
# MAIN
# =============================================================================
def main():
    teams = json.loads((OUTPUT_DIR / "teams.json").read_text(encoding="utf-8"))
    matches = json.loads((OUTPUT_DIR / "matches.json").read_text(encoding="utf-8"))
    by_code = {t["code"]: t for t in teams}

    # 1) Predicciones por partido (fase de grupos)
    print("Generando predicciones de fase de grupos...")
    group_preds = predict_group_stage(by_code, matches)
    (OUTPUT_DIR / "predictions.json").write_text(
        json.dumps(group_preds, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  ✓ {len(group_preds)} predicciones de partidos de grupo")

    # 2) Monte Carlo del torneo
    print(f"\nCorriendo Monte Carlo ({MC_SIMULATIONS} simulaciones)...")
    sims = simulate_tournament(teams, matches, n_sims=MC_SIMULATIONS)
    (OUTPUT_DIR / "simulations.json").write_text(
        json.dumps(sims, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Resumen top 10
    print(f"\nTOP 10 favoritos al título:")
    print(f"{'#':>3}  {'Equipo':<25} {'P(Camp)':>9}  {'P(Final)':>9}  {'P(SF)':>9}  {'Elo':>6}")
    print("─" * 80)
    for i, s in enumerate(sims[:10], 1):
        t = by_code[s["team_code"]]
        print(f"{i:>3}  {t['flag_emoji']} {t['name']:<23} {s['prob_winner']*100:>7.1f}%  {s['prob_finalist']*100:>7.1f}%  {s['prob_semifinal']*100:>7.1f}%  {t['elo_rating']:>6.0f}")

    # Bottom 5
    print(f"\nBOTTOM 5 (probabilidad baja de avanzar):")
    bottom = sorted(sims, key=lambda r: r["prob_winner"])[:5]
    for s in bottom:
        t = by_code[s["team_code"]]
        print(f"      {t['flag_emoji']} {t['name']:<25} P(Camp)={s['prob_winner']*100:.2f}%  P(R16)={s['prob_round_of_16']*100:.1f}%")


if __name__ == "__main__":
    main()
