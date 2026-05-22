-- =============================================================================
-- Migration 0003: tournament outcomes + top scorers
-- =============================================================================
-- Tablas para almacenar:
-- - Predicciones agregadas del podio (campeon, subcampeon, 3er, 4to)
-- - Predicciones de scoreline EXACTO por cada partido (incluye knockouts)
-- - Top scorers (Bota de Oro)
-- =============================================================================

-- Resultado del podio en cada simulación (agregado)
CREATE TABLE IF NOT EXISTS wc_tournament_outcomes (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  model_version   TEXT NOT NULL DEFAULT 'v2',
  n_simulations   INT NOT NULL,
  -- Probabilidad de cada equipo de obtener cada lugar del podio
  team_code       TEXT NOT NULL REFERENCES wc_teams(code),
  prob_champion       NUMERIC(5,4) NOT NULL,
  prob_runner_up      NUMERIC(5,4) NOT NULL,
  prob_third          NUMERIC(5,4) NOT NULL,
  prob_fourth         NUMERIC(5,4) NOT NULL,
  prob_podium         NUMERIC(5,4) NOT NULL,    -- top 3
  generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(team_code, model_version)
);

CREATE INDEX idx_wc_tourn_champ ON wc_tournament_outcomes(prob_champion DESC);

-- Top goleador predicho (Bota de Oro)
CREATE TABLE IF NOT EXISTS wc_top_scorers (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  model_version   TEXT NOT NULL DEFAULT 'v2',
  player_name     TEXT NOT NULL,
  team_code       TEXT NOT NULL REFERENCES wc_teams(code),
  position        TEXT,                          -- FWD principalmente
  predicted_goals NUMERIC(4,2) NOT NULL,         -- goles esperados en el torneo
  prob_top_scorer NUMERIC(5,4) NOT NULL,         -- probabilidad de Bota de Oro
  prob_5_plus     NUMERIC(5,4),                  -- prob de marcar 5+ goles
  generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(player_name, team_code, model_version)
);

CREATE INDEX idx_wc_scorers_goals ON wc_top_scorers(predicted_goals DESC);
CREATE INDEX idx_wc_scorers_team ON wc_top_scorers(team_code);

-- Predicciones de knockout (extendemos wc_predictions a TODAS las fases, no solo grupo)
-- La tabla wc_predictions ya existe, solo agregamos predicciones para R32/R16/QF/SF/3rd/Final
-- via Monte Carlo: para cada match TBD, qué equipos son los más probables que lleguen ahí
-- y cuál es el scoreline esperado.

-- Vista combinada con outcomes del podio
CREATE OR REPLACE VIEW wc_v_podium AS
SELECT
  t.code, t.name, t.flag_emoji, t.confederation, t.group_letter, t.elo_rating,
  o.prob_champion, o.prob_runner_up, o.prob_third, o.prob_fourth, o.prob_podium,
  s.prob_winner, s.prob_finalist, s.prob_semifinal, s.prob_quarterfinal, s.prob_round_of_16
FROM wc_teams t
LEFT JOIN wc_tournament_outcomes o ON o.team_code = t.code
LEFT JOIN wc_simulations s ON s.team_code = t.code
ORDER BY o.prob_champion DESC NULLS LAST;

GRANT SELECT ON wc_v_podium TO anon, authenticated;

-- RLS para nuevas tablas
ALTER TABLE wc_tournament_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE wc_top_scorers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS wc_tournament_outcomes_select_all ON wc_tournament_outcomes;
DROP POLICY IF EXISTS wc_top_scorers_select_all ON wc_top_scorers;
CREATE POLICY wc_tournament_outcomes_select_all ON wc_tournament_outcomes FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY wc_top_scorers_select_all ON wc_top_scorers FOR SELECT TO anon, authenticated USING (true);
