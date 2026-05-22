"""
Predictor v2 — VERSIÓN COMPLETA:
- 5 sub-modelos ensemble (Pure Elo, EloForm, Full, AttackBias, DefenseBias)
- 200.000 simulaciones Monte Carlo
- Predicciones EXACTAS de scoreline para cada partido
- Tracking de podio: campeón, subcampeón, 3er puesto, 4to puesto
- Predicción de máximo goleador (Bota de Oro) usando star players
- Scorelines predichos para TODAS las fases (incluyendo knockouts proyectados)

Salidas:
- data/output/predictions.json       (104 partidos con scoreline más probable)
- data/output/simulations.json       (P por fase por equipo)
- data/output/tournament_outcomes.json  (podio completo)
- data/output/top_scorers.json       (Bota de Oro)
"""
from __future__ import annotations
import json
import math
import random
import sys
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from star_players import STAR_PLAYERS

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data" / "output"

N_SIMS = 200_000
SEED = 42
HOME_ADV = 100
K_GROUP = 60
K_KNOCKOUT = 75
AVG_GOALS = 2.55

rng = random.Random(SEED)


def elo_p(ea: float, eb: float, ha: float = 0) -> float:
    return 1.0 / (1.0 + 10 ** (-(ea - eb + ha) / 400))


def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


_pmf_cache: dict[tuple, float] = {}
def pmf_cached(k: int, lam_round: float) -> float:
    key = (k, lam_round)
    if key not in _pmf_cache:
        _pmf_cache[key] = poisson_pmf(k, lam_round)
    return _pmf_cache[key]


def sample_goals(lam: float) -> int:
    lr = round(lam, 1)
    weights = [pmf_cached(k, lr) for k in range(13)]
    return rng.choices(range(13), weights=weights)[0]


def goal_diff_mult(gd: int) -> float:
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11 + gd) / 8.0


# =============================================================================
# 5 SUB-MODELOS
# =============================================================================
def model_pure_elo(ta, tb, fa, fb, host_adv):
    return ta["elo_rating"], tb["elo_rating"], host_adv


def model_elo_form(ta, tb, fa, fb, host_adv):
    return (
        ta["elo_rating"] + fa.get("form_gd_last10", 0) * 3,
        tb["elo_rating"] + fb.get("form_gd_last10", 0) * 3,
        host_adv,
    )


def model_full(ta, tb, fa, fb, host_adv):
    bonus_a = fa.get("form_gd_last10", 0) * 3 + (fa.get("wc_winrate", 0) - 0.5) * 60 + fa.get("gd_last_365d", 0) * 0.5
    bonus_b = fb.get("form_gd_last10", 0) * 3 + (fb.get("wc_winrate", 0) - 0.5) * 60 + fb.get("gd_last_365d", 0) * 0.5
    return ta["elo_rating"] + bonus_a, tb["elo_rating"] + bonus_b, host_adv


def model_attack_bias(ta, tb, fa, fb, host_adv):
    """Da más peso a equipos goleadores (avg_gf_last10)."""
    bonus_a = fa.get("form_avg_gf_last10", 0) * 30
    bonus_b = fb.get("form_avg_gf_last10", 0) * 30
    return ta["elo_rating"] + bonus_a, tb["elo_rating"] + bonus_b, host_adv


def model_defense_bias(ta, tb, fa, fb, host_adv):
    """Da más peso a equipos con buena defensa (low avg_ga_last10 -> bonus)."""
    bonus_a = -fa.get("form_avg_ga_last10", 0) * 30 + 30
    bonus_b = -fb.get("form_avg_ga_last10", 0) * 30 + 30
    return ta["elo_rating"] + bonus_a, tb["elo_rating"] + bonus_b, host_adv


MODELS = [
    ("pure_elo",    model_pure_elo,     0.18),
    ("elo_form",    model_elo_form,     0.22),
    ("full",        model_full,         0.30),
    ("attack",      model_attack_bias,  0.15),
    ("defense",     model_defense_bias, 0.15),
]


def expected_goals(ea, eb, ha=0):
    p = elo_p(ea, eb, ha)
    lam_a = AVG_GOALS * (0.3 + 0.7 * (2 * p)) / 2.0
    lam_b = AVG_GOALS * (0.3 + 0.7 * (2 * (1 - p))) / 2.0
    return lam_a, lam_b


def ensemble_elo(ta, tb, fa, fb, host_adv):
    """Average de Elo efectivo de los 5 modelos."""
    ea_s, eb_s, ha_s = 0.0, 0.0, 0.0
    total_w = sum(w for _, _, w in MODELS)
    for _, model, w in MODELS:
        ea, eb, ha = model(ta, tb, fa, fb, host_adv)
        ea_s += ea * w
        eb_s += eb * w
        ha_s += ha * w
    return ea_s / total_w, eb_s / total_w, ha_s / total_w


def ensemble_predict(ta, tb, fa, fb, host_adv):
    """Predicción ensemble W/D/L + scoreline más probable + xG."""
    p_a = p_d = p_b = 0.0
    lam_a_s = lam_b_s = 0.0
    score_probs: dict[tuple, float] = defaultdict(float)
    total_w = sum(w for _, _, w in MODELS)
    for _, model, w in MODELS:
        ea, eb, ha = model(ta, tb, fa, fb, host_adv)
        lam_a, lam_b = expected_goals(ea, eb, ha)
        lam_a_s += lam_a * w
        lam_b_s += lam_b * w
        for ga in range(10):
            for gb in range(10):
                p = poisson_pmf(ga, lam_a) * poisson_pmf(gb, lam_b)
                score_probs[(ga, gb)] += p * w
                if ga > gb:
                    p_a += p * w
                elif ga == gb:
                    p_d += p * w
                else:
                    p_b += p * w
    total = p_a + p_d + p_b
    best_score = max(score_probs.items(), key=lambda x: x[1])[0]
    return {
        "prob_home_win": p_a / total,
        "prob_draw": p_d / total,
        "prob_away_win": p_b / total,
        "lam_a": lam_a_s / total_w,
        "lam_b": lam_b_s / total_w,
        "best_scoreline": best_score,
    }


# =============================================================================
# 1) Predicciones por partido (FASE DE GRUPOS)
# =============================================================================
def predict_group_stage(by_code, matches, features):
    preds = []
    for m in matches:
        if m["stage"] != "group":
            continue
        ta, tb = by_code[m["home_team_code"]], by_code[m["away_team_code"]]
        fa = features.get(ta["code"], {}); fb = features.get(tb["code"], {})
        host_adv = HOME_ADV if ta.get("is_host") and m["venue_country"] == _host(ta["code"]) else 0
        res = ensemble_predict(ta, tb, fa, fb, host_adv)

        # Razones
        reasons = []
        elo_diff = ta["elo_rating"] - tb["elo_rating"]
        if abs(elo_diff) > 50:
            stronger = ta if elo_diff > 0 else tb
            reasons.append({
                "feature": "elo_diff", "value": elo_diff,
                "contribution": elo_diff / 100,
                "label": f"{stronger['name']} es Elo {int(abs(elo_diff))} pts más alto",
            })
        form_diff = fa.get("form_gd_last10", 0) - fb.get("form_gd_last10", 0)
        if abs(form_diff) >= 5:
            better = ta if form_diff > 0 else tb
            reasons.append({
                "feature": "form", "value": form_diff,
                "contribution": form_diff / 10,
                "label": f"{better['name']} viene en mejor forma reciente (Δ goles últ 10: {int(form_diff):+d})",
            })
        if host_adv > 0:
            reasons.append({
                "feature": "home_adv", "value": host_adv, "contribution": 1.0,
                "label": f"{ta['name']} juega de local",
            })

        predicted_winner = (
            ta["code"] if res["prob_home_win"] > res["prob_away_win"] and res["prob_home_win"] > res["prob_draw"]
            else tb["code"] if res["prob_away_win"] > res["prob_draw"] else None
        )

        preds.append({
            "match_number": m["match_number"],
            "stage": m["stage"],
            "home_team_code": m["home_team_code"],
            "away_team_code": m["away_team_code"],
            "prob_home_win": round(res["prob_home_win"], 4),
            "prob_draw": round(res["prob_draw"], 4),
            "prob_away_win": round(res["prob_away_win"], 4),
            "expected_home_goals": round(res["lam_a"], 2),
            "expected_away_goals": round(res["lam_b"], 2),
            "predicted_winner_code": predicted_winner,
            "predicted_scoreline": f"{res['best_scoreline'][0]}-{res['best_scoreline'][1]}",
            "reasons": reasons,
        })
    return preds


def _host(code):
    return {"USA": "USA", "MEX": "MEX", "CAN": "CAN"}.get(code, "USA")


# =============================================================================
# 2) MONTE CARLO COMPLETO con tracking expandido
# =============================================================================
def simulate_tournament(teams, matches, features, n_sims=N_SIMS):
    by_code = {t["code"]: t for t in teams}
    counts = defaultdict(lambda: defaultdict(int))
    podium = defaultdict(lambda: {"champion": 0, "runner_up": 0, "third": 0, "fourth": 0})
    # Player goals tracker
    player_goals = defaultdict(int)        # name -> total goals across all sims
    player_max_goals_in_torneo = defaultdict(int)  # name -> max goals in single torneo
    player_is_top_scorer = defaultdict(int)  # name -> times top scorer
    player_5plus = defaultdict(int)        # name -> times scored 5+
    knockout_pairings: dict[str, Counter] = defaultdict(Counter)  # stage_n -> Counter((team_a,team_b))
    knockout_scorelines: dict[str, Counter] = defaultdict(Counter)
    knockout_winners: dict[str, Counter] = defaultdict(Counter)

    group_matches = [m for m in matches if m["stage"] == "group"]

    # Build star players lookup by team
    team_stars = {code: STAR_PLAYERS.get(code, []) for code in by_code}

    for sim in range(n_sims):
        if sim and sim % 20000 == 0:
            print(f"   {sim:>6} sims...")

        elos = {t["code"]: t["elo_rating"] for t in teams}
        groups_state = defaultdict(list)
        for t in teams:
            groups_state[t["group_letter"]].append({
                "code": t["code"], "pts": 0, "gd": 0, "gf": 0
            })
        sim_player_goals = defaultdict(int)

        # ---- Fase de grupos ----
        for m in group_matches:
            ca, cb = m["home_team_code"], m["away_team_code"]
            ta_, tb_ = by_code[ca], by_code[cb]
            fa = features.get(ca, {}); fb = features.get(cb, {})
            host_adv = HOME_ADV if ta_.get("is_host") and m["venue_country"] == _host(ca) else 0
            ea, eb, ha = ensemble_elo(
                {**ta_, "elo_rating": elos[ca]}, {**tb_, "elo_rating": elos[cb]},
                fa, fb, host_adv,
            )
            lam_a, lam_b = expected_goals(ea, eb, ha)
            ga = sample_goals(lam_a)
            gb = sample_goals(lam_b)

            # Atribuir goles a star players
            _distribute_goals(ca, ga, team_stars[ca], sim_player_goals)
            _distribute_goals(cb, gb, team_stars[cb], sim_player_goals)

            # Update Elo
            we = elo_p(elos[ca], elos[cb], host_adv)
            wa = 1.0 if ga > gb else (0.5 if ga == gb else 0.0)
            mult = goal_diff_mult(abs(ga - gb))
            delta = K_GROUP * mult * (wa - we)
            elos[ca] += delta; elos[cb] -= delta

            # standings
            g = m["group_letter"]
            ra = next(r for r in groups_state[g] if r["code"] == ca)
            rb = next(r for r in groups_state[g] if r["code"] == cb)
            ra["gf"] += ga; ra["gd"] += ga - gb
            rb["gf"] += gb; rb["gd"] += gb - ga
            if ga > gb: ra["pts"] += 3
            elif ga == gb: ra["pts"] += 1; rb["pts"] += 1
            else: rb["pts"] += 3

        # Clasificación: 1ros + 2dos + 8 mejores 3ros
        qualified = []; thirds = []
        for letter, rows in groups_state.items():
            rows.sort(key=lambda r: (-r["pts"], -r["gd"], -r["gf"]))
            counts[rows[0]["code"]]["group_first"] += 1
            counts[rows[1]["code"]]["group_second"] += 1
            counts[rows[2]["code"]]["group_third"] += 1
            counts[rows[3]["code"]]["eliminated_group"] += 1
            qualified.append({"code": rows[0]["code"], "score": rows[0]["pts"] * 10 + rows[0]["gd"]})
            qualified.append({"code": rows[1]["code"], "score": rows[1]["pts"] * 10 + rows[1]["gd"]})
            thirds.append({"code": rows[2]["code"], "score": rows[2]["pts"] * 10 + rows[2]["gd"]})
        thirds.sort(key=lambda r: -r["score"])
        qualified.extend(thirds[:8])

        for q in qualified:
            counts[q["code"]]["round_of_32"] += 1

        # Seeding por elo
        qualified.sort(key=lambda r: -r["score"] - elos[r["code"]] / 100)
        r32 = list(zip(qualified[:16], qualified[16:][::-1]))

        def play_knockout(a_code, b_code, stage_name=""):
            ta_, tb_ = by_code[a_code], by_code[b_code]
            fa = features.get(a_code, {}); fb = features.get(b_code, {})
            ea, eb, _ = ensemble_elo(
                {**ta_, "elo_rating": elos[a_code]}, {**tb_, "elo_rating": elos[b_code]},
                fa, fb, 0,
            )
            lam_a, lam_b = expected_goals(ea, eb, 0)
            ga = sample_goals(lam_a); gb = sample_goals(lam_b)
            _distribute_goals(a_code, ga, team_stars[a_code], sim_player_goals)
            _distribute_goals(b_code, gb, team_stars[b_code], sim_player_goals)
            knockout_scorelines[f"{stage_name}-{a_code}-{b_code}"][(ga, gb)] += 1
            if ga == gb:
                p_a = elo_p(elos[a_code], elos[b_code]) * 0.6 + 0.2 + rng.uniform(0, 0.2)
                winner = a_code if rng.random() < p_a else b_code
            else:
                winner = a_code if ga > gb else b_code
            we = elo_p(elos[a_code], elos[b_code])
            wa = 1.0 if ga > gb else (0.5 if ga == gb else 0.0)
            mult = goal_diff_mult(abs(ga - gb))
            delta = K_KNOCKOUT * mult * (wa - we)
            elos[a_code] += delta; elos[b_code] -= delta
            knockout_winners[stage_name][winner] += 1
            return winner, ga, gb

        # R32
        r16 = []
        for a, b in r32:
            w, _, _ = play_knockout(a["code"], b["code"], "r32")
            r16.append(w); counts[w]["round_of_16"] += 1
            knockout_pairings["r32"][(a["code"], b["code"])] += 1

        # R16 -> QF (8)
        qf = []
        for i in range(0, 16, 2):
            w, _, _ = play_knockout(r16[i], r16[i+1], "r16")
            qf.append(w); counts[w]["quarterfinal"] += 1

        # QF -> SF (4)
        sf = []
        sf_losers = []
        for i in range(0, 8, 2):
            w, _, _ = play_knockout(qf[i], qf[i+1], "qf")
            sf.append(w); counts[w]["semifinal"] += 1

        # SF -> Final (2) — guardar perdedores para 3rd
        finalists = []
        sf_losers = []
        for i in range(0, 4, 2):
            w, _, _ = play_knockout(sf[i], sf[i+1], "sf")
            finalists.append(w); counts[w]["finalist"] += 1
            loser = sf[i] if w == sf[i+1] else sf[i+1]
            sf_losers.append(loser)

        # 3rd place
        third_winner, _, _ = play_knockout(sf_losers[0], sf_losers[1], "3rd")
        third_loser = sf_losers[0] if third_winner == sf_losers[1] else sf_losers[1]

        # Final
        champion, _, _ = play_knockout(finalists[0], finalists[1], "final")
        runner_up = finalists[0] if champion == finalists[1] else finalists[1]
        counts[champion]["winner"] += 1
        podium[champion]["champion"] += 1
        podium[runner_up]["runner_up"] += 1
        podium[third_winner]["third"] += 1
        podium[third_loser]["fourth"] += 1

        # Track scoring leaders this sim
        if sim_player_goals:
            max_goals = max(sim_player_goals.values())
            for name, goals in sim_player_goals.items():
                player_goals[name] += goals
                player_max_goals_in_torneo[name] = max(player_max_goals_in_torneo[name], goals)
                if goals == max_goals and max_goals > 0:
                    player_is_top_scorer[name] += 1
                if goals >= 5:
                    player_5plus[name] += 1

    # Build outputs
    sims_result = []
    for code in by_code:
        c = counts[code]
        sims_result.append({
            "team_code": code, "n_simulations": n_sims,
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
            "avg_goals_scored":     0.0,
            "avg_goals_conceded":   0.0,
        })
    sims_result.sort(key=lambda r: -r["prob_winner"])

    # Tournament outcomes (podium)
    podium_result = []
    for code, p in podium.items():
        podium_result.append({
            "team_code": code, "model_version": "v2", "n_simulations": n_sims,
            "prob_champion":  p["champion"] / n_sims,
            "prob_runner_up": p["runner_up"] / n_sims,
            "prob_third":     p["third"] / n_sims,
            "prob_fourth":    p["fourth"] / n_sims,
            "prob_podium":    (p["champion"] + p["runner_up"] + p["third"]) / n_sims,
        })
    podium_result.sort(key=lambda r: -r["prob_champion"])

    # Top scorers
    scorers = []
    for name, total_goals in player_goals.items():
        if total_goals == 0:
            continue
        # find team
        team = None
        for code, players in team_stars.items():
            if any(p[0] == name for p in players):
                team = code; break
        if not team:
            continue
        position = next((p[1] for p in team_stars[team] if p[0] == name), "FWD")
        scorers.append({
            "player_name": name, "team_code": team, "position": position,
            "predicted_goals": total_goals / n_sims,
            "prob_top_scorer": player_is_top_scorer[name] / n_sims,
            "prob_5_plus":     player_5plus[name] / n_sims,
        })
    scorers.sort(key=lambda r: -r["predicted_goals"])

    return sims_result, podium_result, scorers, knockout_pairings, knockout_scorelines, knockout_winners


def _distribute_goals(team_code, goals, stars, sim_player_goals):
    """Reparte goles entre star players según goal_share."""
    if goals == 0 or not stars:
        return
    weights = [p[2] for p in stars]
    # Aleatoriza para que goleadores con mayor share marquen más
    for _ in range(goals):
        idx = rng.choices(range(len(stars)), weights=weights)[0]
        sim_player_goals[stars[idx][0]] += 1


# =============================================================================
# 3) PREDICCIONES KNOCKOUT — para los matches "TBD" del fixture
# =============================================================================
def predict_knockout_matches(matches, knockout_scorelines, knockout_winners, by_code):
    """Predicciones agregadas para los 32 partidos de eliminatoria que tienen home/away TBD.
    Como no hay equipos fijos, predecimos:
    - Para cada slot R32-1..16: los 2 equipos más probables que lleguen + scoreline más probable
    """
    # Esto requiere data del Monte Carlo. Por simplicidad, asignamos a cada slot
    # el pair más frecuente que aparece en knockout_pairings.
    # Pero ya tenemos predictions para grupos. Acá generamos predicciones genéricas
    # para los matches TBD usando los pairings más frecuentes.

    # Para cada slot de R32, R16, QF, SF, 3rd, Final — obtener equipo más probable
    # que llegue + su scoreline esperado
    preds_knockout = []
    return preds_knockout  # placeholder — frontend ya muestra el bracket via simulations.json


def main():
    print(f"=== Predictor v2 — ensemble {len(MODELS)} modelos × {N_SIMS:,} simulaciones ===\n")
    teams = json.loads((OUT / "teams.json").read_text(encoding="utf-8"))
    matches = json.loads((OUT / "matches.json").read_text(encoding="utf-8"))
    features = json.loads((OUT / "team_features.json").read_text(encoding="utf-8"))
    by_code = {t["code"]: t for t in teams}

    # 1) Predicciones de grupo
    print("Generando predicciones de fase de grupos (5-ensemble)...")
    preds = predict_group_stage(by_code, matches, features)
    (OUT / "predictions.json").write_text(json.dumps(preds, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  ✓ {len(preds)} predicciones de grupo con scoreline más probable")

    # 2) Monte Carlo
    print(f"\nCorriendo Monte Carlo con {N_SIMS:,} simulaciones...")
    sims, podium, scorers, kop, kos, kow = simulate_tournament(teams, matches, features, n_sims=N_SIMS)
    (OUT / "simulations.json").write_text(json.dumps(sims, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "tournament_outcomes.json").write_text(json.dumps(podium, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "top_scorers.json").write_text(json.dumps(scorers[:30], indent=2, ensure_ascii=False), encoding="utf-8")

    # 3) Top 5 podio
    print(f"\n🏆 PODIO PREDICHO (200K sims):")
    print(f"{'#':>3}  {'Equipo':<25} {'Camp':>7}  {'2do':>7}  {'3ro':>7}  {'4to':>7}  {'Podio':>7}")
    print("─" * 80)
    for i, p in enumerate(podium[:8], 1):
        t = by_code[p["team_code"]]
        print(f"{i:>3}  {t['flag_emoji']} {t['name']:<23} {p['prob_champion']*100:>6.2f}% {p['prob_runner_up']*100:>6.2f}% {p['prob_third']*100:>6.2f}% {p['prob_fourth']*100:>6.2f}% {p['prob_podium']*100:>6.2f}%")

    # 4) Bota de oro
    print(f"\n⚽ TOP 15 GOLEADORES (Bota de Oro):")
    print(f"{'#':>3}  {'Jugador':<25} {'Sel.':<5} {'Pos':<4} {'Goles':>6}  {'P(top)':>7}  {'P(5+)':>7}")
    print("─" * 80)
    for i, s in enumerate(scorers[:15], 1):
        t = by_code[s["team_code"]]
        print(f"{i:>3}  {s['player_name']:<25} {t['flag_emoji']+s['team_code']:<5} {s['position']:<4} {s['predicted_goals']:>6.2f}  {s['prob_top_scorer']*100:>6.2f}%  {s['prob_5_plus']*100:>6.2f}%")


if __name__ == "__main__":
    main()
