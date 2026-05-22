"""
Predictor avanzado:
- Ensemble de 3 modelos (Elo puro, Elo+Form, Elo+Form+WC Pedigree)
- 100K simulaciones Monte Carlo del torneo
- Features: Elo + form últimos 10 + winrate Mundial + gd último año
- Outputs calibrados

Reemplaza predictions.json + simulations.json con resultados más robustos.
"""
from __future__ import annotations
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data" / "output"

# Parámetros
N_SIMS = 100_000
SEED = 42
HOME_ADV = 100
K_GROUP = 60
K_KNOCKOUT = 75
AVG_GOALS = 2.55

rng = random.Random(SEED)


# =============================================================================
# Helpers Elo + Poisson
# =============================================================================
def elo_p(ea: float, eb: float, ha: float = 0) -> float:
    return 1.0 / (1.0 + 10 ** (-(ea - eb + ha) / 400))


def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def sample_goals(lam: float, max_g: int = 12) -> int:
    weights = [poisson_pmf(k, lam) for k in range(max_g)]
    return rng.choices(range(max_g), weights=weights)[0]


def goal_diff_mult(gd: int) -> float:
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11 + gd) / 8.0


# =============================================================================
# Tres modelos
# =============================================================================
def model_pure_elo(t_a, t_b, _f_a, _f_b, host_adv):
    """Modelo 1: solo Elo."""
    return t_a["elo_rating"], t_b["elo_rating"], host_adv


def model_elo_form(t_a, t_b, f_a, f_b, host_adv):
    """Modelo 2: Elo + ajuste por form últimos 10."""
    bonus_a = (f_a.get("form_gd_last10", 0) - 0) * 3  # 3 Elo per goal diff
    bonus_b = (f_b.get("form_gd_last10", 0) - 0) * 3
    return t_a["elo_rating"] + bonus_a, t_b["elo_rating"] + bonus_b, host_adv


def model_full(t_a, t_b, f_a, f_b, host_adv):
    """Modelo 3: Elo + form + WC pedigree + actividad reciente."""
    # form
    bonus_a = (f_a.get("form_gd_last10", 0)) * 3
    bonus_b = (f_b.get("form_gd_last10", 0)) * 3
    # WC pedigree (boost para equipos con historia ganadora en mundiales)
    bonus_a += (f_a.get("wc_winrate", 0) - 0.5) * 60
    bonus_b += (f_b.get("wc_winrate", 0) - 0.5) * 60
    # actividad año (proxy de "están en forma este ciclo")
    bonus_a += (f_a.get("gd_last_365d", 0)) * 0.5
    bonus_b += (f_b.get("gd_last_365d", 0)) * 0.5
    return t_a["elo_rating"] + bonus_a, t_b["elo_rating"] + bonus_b, host_adv


MODELS = [
    ("pure_elo", model_pure_elo, 0.30),
    ("elo_form", model_elo_form, 0.35),
    ("full", model_full, 0.35),
]


def expected_goals(elo_a: float, elo_b: float, ha: float = 0) -> tuple[float, float]:
    p_a = elo_p(elo_a, elo_b, ha)
    lam_a = AVG_GOALS * (0.3 + 0.7 * (2 * p_a)) / 2.0
    lam_b = AVG_GOALS * (0.3 + 0.7 * (2 * (1 - p_a))) / 2.0
    return lam_a, lam_b


def ensemble_predict(t_a, t_b, f_a, f_b, host_adv):
    """Predicción ensemble: promedio ponderado de las 3 prob de victoria."""
    p_a_win = 0.0
    p_draw = 0.0
    p_b_win = 0.0
    lam_a_sum = 0.0
    lam_b_sum = 0.0
    total_w = sum(w for _, _, w in MODELS)
    for name, model, w in MODELS:
        ea, eb, ha = model(t_a, t_b, f_a, f_b, host_adv)
        lam_a, lam_b = expected_goals(ea, eb, ha)
        lam_a_sum += lam_a * w
        lam_b_sum += lam_b * w
        # Compute outcome
        pa, pd, pb = 0.0, 0.0, 0.0
        for ga in range(11):
            for gb in range(11):
                p = poisson_pmf(ga, lam_a) * poisson_pmf(gb, lam_b)
                if ga > gb:
                    pa += p
                elif ga == gb:
                    pd += p
                else:
                    pb += p
        p_a_win += pa * w
        p_draw += pd * w
        p_b_win += pb * w
    # Normalizar
    total = p_a_win + p_draw + p_b_win
    return {
        "prob_home_win": p_a_win / total,
        "prob_draw": p_draw / total,
        "prob_away_win": p_b_win / total,
        "lam_a": lam_a_sum / total_w,
        "lam_b": lam_b_sum / total_w,
    }


def ensemble_elo(t_a, t_b, f_a, f_b, host_adv):
    """Devuelve Elo efectivo del ensemble (para Monte Carlo sample)."""
    ea_sum, eb_sum, ha_sum = 0.0, 0.0, 0.0
    total_w = sum(w for _, _, w in MODELS)
    for name, model, w in MODELS:
        ea, eb, ha = model(t_a, t_b, f_a, f_b, host_adv)
        ea_sum += ea * w
        eb_sum += eb * w
        ha_sum += ha * w
    return ea_sum / total_w, eb_sum / total_w, ha_sum / total_w


# =============================================================================
# Predicciones por partido (fase de grupos)
# =============================================================================
def predict_group_stage(teams_by_code, matches, features):
    preds = []
    for m in matches:
        if m["stage"] != "group":
            continue
        ta = teams_by_code[m["home_team_code"]]
        tb = teams_by_code[m["away_team_code"]]
        fa = features.get(ta["code"], {})
        fb = features.get(tb["code"], {})
        host_adv = HOME_ADV if ta.get("is_host") and m["venue_country"] == _host(ta["code"]) else 0
        result = ensemble_predict(ta, tb, fa, fb, host_adv)

        # Score más probable
        best = (0, 0)
        best_p = 0
        for ga in range(8):
            for gb in range(8):
                p = poisson_pmf(ga, result["lam_a"]) * poisson_pmf(gb, result["lam_b"])
                if p > best_p:
                    best_p = p
                    best = (ga, gb)

        reasons = []
        elo_diff = ta["elo_rating"] - tb["elo_rating"]
        if abs(elo_diff) > 50:
            stronger = ta if elo_diff > 0 else tb
            reasons.append({
                "feature": "elo_diff",
                "value": elo_diff,
                "contribution": elo_diff / 100,
                "label": f"{stronger['name']} es Elo {int(abs(elo_diff))} pts más alto",
            })
        form_diff = fa.get("form_gd_last10", 0) - fb.get("form_gd_last10", 0)
        if abs(form_diff) >= 5:
            better = ta if form_diff > 0 else tb
            reasons.append({
                "feature": "form",
                "value": form_diff,
                "contribution": form_diff / 10,
                "label": f"{better['name']} viene con mejor forma reciente (Δ goles últimos 10: {int(form_diff):+d})",
            })
        wc_diff = fa.get("wc_winrate", 0) - fb.get("wc_winrate", 0)
        if abs(wc_diff) > 0.15:
            better = ta if wc_diff > 0 else tb
            reasons.append({
                "feature": "wc_pedigree",
                "value": wc_diff,
                "contribution": wc_diff,
                "label": f"{better['name']} tiene mejor historial en Mundiales (winrate {int((better is ta and fa or fb).get('wc_winrate', 0) * 100)}%)",
            })
        if host_adv > 0:
            reasons.append({
                "feature": "home_advantage",
                "value": host_adv,
                "contribution": 1.0,
                "label": f"{ta['name']} juega de local en su país",
            })

        predicted_winner = (
            ta["code"] if result["prob_home_win"] > result["prob_away_win"] and result["prob_home_win"] > result["prob_draw"]
            else tb["code"] if result["prob_away_win"] > result["prob_draw"]
            else None
        )

        preds.append({
            "match_number": m["match_number"],
            "stage": m["stage"],
            "home_team_code": m["home_team_code"],
            "away_team_code": m["away_team_code"],
            "prob_home_win": round(result["prob_home_win"], 4),
            "prob_draw": round(result["prob_draw"], 4),
            "prob_away_win": round(result["prob_away_win"], 4),
            "expected_home_goals": round(result["lam_a"], 2),
            "expected_away_goals": round(result["lam_b"], 2),
            "predicted_winner_code": predicted_winner,
            "predicted_scoreline": f"{best[0]}-{best[1]}",
            "reasons": reasons,
        })
    return preds


def _host(code):
    return {"USA": "USA", "MEX": "MEX", "CAN": "CAN"}.get(code, "USA")


# =============================================================================
# Monte Carlo simulator
# =============================================================================
def simulate_tournament(teams, matches, features, n_sims=N_SIMS):
    by_code = {t["code"]: t for t in teams}
    counts = defaultdict(lambda: defaultdict(int))
    goals_scored = defaultdict(int)
    goals_conceded = defaultdict(int)

    group_matches = [m for m in matches if m["stage"] == "group"]

    for sim in range(n_sims):
        if sim and sim % 10000 == 0:
            print(f"   {sim:>6} simulaciones...")

        elos = {t["code"]: t["elo_rating"] for t in teams}
        groups = defaultdict(list)
        for t in teams:
            groups[t["group_letter"]].append({"code": t["code"], "pts": 0, "gd": 0, "gf": 0})

        # Fase de grupos
        for m in group_matches:
            ca, cb = m["home_team_code"], m["away_team_code"]
            ta_, tb_ = by_code[ca], by_code[cb]
            fa = features.get(ca, {})
            fb = features.get(cb, {})
            host_adv = HOME_ADV if ta_.get("is_host") and m["venue_country"] == _host(ca) else 0
            # Use ensemble Elo effectivo
            ea, eb, ha = ensemble_elo(
                {"elo_rating": elos[ca], **{k: v for k, v in ta_.items() if k != "elo_rating"}},
                {"elo_rating": elos[cb], **{k: v for k, v in tb_.items() if k != "elo_rating"}},
                fa, fb, host_adv,
            )
            lam_a, lam_b = expected_goals(ea, eb, ha)
            ga = sample_goals(lam_a)
            gb = sample_goals(lam_b)
            # Update Elo (real values without bonuses)
            we = elo_p(elos[ca], elos[cb], host_adv)
            wa = 1.0 if ga > gb else (0.5 if ga == gb else 0.0)
            mult = goal_diff_mult(abs(ga - gb))
            delta = K_GROUP * mult * (wa - we)
            elos[ca] += delta
            elos[cb] -= delta
            # Update standings
            g = m["group_letter"]
            ra = next(r for r in groups[g] if r["code"] == ca)
            rb = next(r for r in groups[g] if r["code"] == cb)
            ra["gf"] += ga; ra["gd"] += ga - gb
            rb["gf"] += gb; rb["gd"] += gb - ga
            if ga > gb: ra["pts"] += 3
            elif ga == gb: ra["pts"] += 1; rb["pts"] += 1
            else: rb["pts"] += 3
            goals_scored[ca] += ga; goals_conceded[ca] += gb
            goals_scored[cb] += gb; goals_conceded[cb] += ga

        # Determine 32 qualified
        qualified = []; thirds = []
        for letter, rows in groups.items():
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

        # Pair by ranking
        qualified.sort(key=lambda r: -r["score"] - elos[r["code"]] / 100)
        r32 = list(zip(qualified[:16], qualified[16:][::-1]))

        def play_knockout(a_code, b_code):
            ta_, tb_ = by_code[a_code], by_code[b_code]
            fa = features.get(a_code, {}); fb = features.get(b_code, {})
            ea, eb, _ = ensemble_elo(
                {"elo_rating": elos[a_code], **{k: v for k, v in ta_.items() if k != "elo_rating"}},
                {"elo_rating": elos[b_code], **{k: v for k, v in tb_.items() if k != "elo_rating"}},
                fa, fb, 0,
            )
            lam_a, lam_b = expected_goals(ea, eb, 0)
            ga = sample_goals(lam_a)
            gb = sample_goals(lam_b)
            goals_scored[a_code] += ga; goals_conceded[a_code] += gb
            goals_scored[b_code] += gb; goals_conceded[b_code] += ga
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
            return winner

        # R32 -> R16
        r16 = []
        for a, b in r32:
            w = play_knockout(a["code"], b["code"])
            r16.append(w); counts[w]["round_of_16"] += 1

        # R16 -> QF
        qf = []
        for i in range(0, 16, 2):
            w = play_knockout(r16[i], r16[i+1])
            qf.append(w); counts[w]["quarterfinal"] += 1

        # QF -> SF
        sf = []
        for i in range(0, 8, 2):
            w = play_knockout(qf[i], qf[i+1])
            sf.append(w); counts[w]["semifinal"] += 1

        # SF -> Final
        finalists = []
        for i in range(0, 4, 2):
            w = play_knockout(sf[i], sf[i+1])
            finalists.append(w); counts[w]["finalist"] += 1

        # Final
        champion = play_knockout(finalists[0], finalists[1])
        counts[champion]["winner"] += 1

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
            "avg_goals_scored":     goals_scored[code] / n_sims,
            "avg_goals_conceded":   goals_conceded[code] / n_sims,
        })
    return sorted(results, key=lambda r: -r["prob_winner"])


def main():
    teams = json.loads((OUT / "teams.json").read_text(encoding="utf-8"))
    matches = json.loads((OUT / "matches.json").read_text(encoding="utf-8"))
    features = json.loads((OUT / "team_features.json").read_text(encoding="utf-8"))
    by_code = {t["code"]: t for t in teams}

    print(f"Modelo ensemble: {len(MODELS)} sub-modelos, pesos {[w for _,_,w in MODELS]}")

    # Predicciones por partido
    print(f"\nGenerando predicciones de fase de grupos (ensemble)...")
    preds = predict_group_stage(by_code, matches, features)
    (OUT / "predictions.json").write_text(
        json.dumps(preds, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  ✓ {len(preds)} predicciones")

    # Monte Carlo
    print(f"\nCorriendo Monte Carlo con {N_SIMS:,} simulaciones (ensemble)...")
    sims = simulate_tournament(teams, matches, features, n_sims=N_SIMS)
    (OUT / "simulations.json").write_text(
        json.dumps(sims, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\nTOP 12 favoritos al título (ensemble, {N_SIMS:,} sims):")
    print(f"{'#':>3}  {'Equipo':<25} {'P(Camp)':>9}  {'P(Final)':>9}  {'P(SF)':>9}  {'Elo':>6}  {'Form':>5}")
    print("─" * 85)
    for i, s in enumerate(sims[:12], 1):
        t = by_code[s["team_code"]]
        f = features.get(t["code"], {})
        form = f.get("form_gd_last10", 0)
        print(f"{i:>3}  {t['flag_emoji']} {t['name']:<23} {s['prob_winner']*100:>7.2f}%  {s['prob_finalist']*100:>7.2f}%  {s['prob_semifinal']*100:>7.2f}%  {t['elo_rating']:>6.0f}  {form:>+5d}")


if __name__ == "__main__":
    main()
