-- =============================================================================
-- Mundial 2026 Predictor — Schema
-- Tables prefixed with wc_ to coexist with EDM tables in same Supabase project
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- TEAMS (48 selecciones del Mundial 2026)
-- =============================================================================
CREATE TABLE IF NOT EXISTS wc_teams (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code            TEXT NOT NULL UNIQUE,        -- ISO 3 letras (ARG, BRA, etc)
  name            TEXT NOT NULL,
  flag_emoji      TEXT,
  confederation   TEXT NOT NULL,               -- UEFA, CONMEBOL, CONCACAF, AFC, CAF, OFC
  group_letter    TEXT NOT NULL,               -- A-L
  group_position  INT,                          -- 1..4 dentro del grupo (seeding)
  is_host         BOOLEAN DEFAULT FALSE,
  fifa_rank       INT,                          -- ranking FIFA al 1 abr 2026
  fifa_points     NUMERIC,
  elo_rating      NUMERIC NOT NULL,            -- Elo actual (eloratings.net)
  manager_name    TEXT,
  is_debut        BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_wc_teams_group ON wc_teams(group_letter, group_position);
CREATE INDEX idx_wc_teams_elo ON wc_teams(elo_rating DESC);

-- =============================================================================
-- PLAYERS (rosters de cada seleccion — editable)
-- =============================================================================
CREATE TABLE IF NOT EXISTS wc_players (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  team_code       TEXT NOT NULL REFERENCES wc_teams(code) ON DELETE CASCADE,
  jersey_number   INT,
  full_name       TEXT NOT NULL,
  position        TEXT CHECK (position IN ('GK', 'DEF', 'MID', 'FWD')),
  club            TEXT,
  club_country    TEXT,
  age             INT,
  caps            INT,
  goals           INT,
  fc26_overall    INT,                          -- rating EA FC26 (1-99)
  market_value_eur BIGINT,                       -- Transfermarkt
  is_captain      BOOLEAN DEFAULT FALSE,
  is_starter      BOOLEAN DEFAULT FALSE,        -- XI titular probable
  is_active       BOOLEAN DEFAULT TRUE,         -- false si lesionado/suspendido
  notes           TEXT,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_wc_players_team ON wc_players(team_code);
CREATE INDEX idx_wc_players_starter ON wc_players(team_code, is_starter);

-- =============================================================================
-- MATCHES (los 104 partidos del fixture WC2026 + resultados reales si ya jugados)
-- =============================================================================
CREATE TABLE IF NOT EXISTS wc_matches (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  match_number    INT NOT NULL UNIQUE,         -- 1..104
  stage           TEXT NOT NULL,               -- group | r32 | r16 | qf | sf | 3rd | final
  group_letter    TEXT,                        -- A-L para fase de grupos
  scheduled_at    TIMESTAMPTZ NOT NULL,
  venue_city      TEXT,
  venue_stadium   TEXT,
  venue_country   TEXT,                        -- USA | MEX | CAN

  home_team_code  TEXT REFERENCES wc_teams(code),
  away_team_code  TEXT REFERENCES wc_teams(code),
  -- Para eliminatorias antes del sorteo, equipos pueden ser TBD: home_label / away_label
  home_label      TEXT,                        -- "Winner Group A" | "2nd Group B" etc
  away_label      TEXT,

  -- Resultados (NULL si aun no se jugo)
  home_score      INT,
  away_score      INT,
  home_pens       INT,
  away_pens       INT,
  status          TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'live', 'finished')),

  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_wc_matches_stage ON wc_matches(stage, scheduled_at);
CREATE INDEX idx_wc_matches_group ON wc_matches(group_letter, scheduled_at);
CREATE INDEX idx_wc_matches_home ON wc_matches(home_team_code);
CREATE INDEX idx_wc_matches_away ON wc_matches(away_team_code);

-- =============================================================================
-- PREDICTIONS (output del modelo ML para cada partido)
-- =============================================================================
CREATE TABLE IF NOT EXISTS wc_predictions (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  match_id        UUID NOT NULL REFERENCES wc_matches(id) ON DELETE CASCADE,
  model_version   TEXT NOT NULL DEFAULT 'v1',

  -- Probabilidades (suman 1.0)
  prob_home_win   NUMERIC(5,4) NOT NULL,
  prob_draw       NUMERIC(5,4) NOT NULL,
  prob_away_win   NUMERIC(5,4) NOT NULL,

  -- Goles esperados (Poisson)
  expected_home_goals NUMERIC(4,2) NOT NULL,
  expected_away_goals NUMERIC(4,2) NOT NULL,

  -- Resultado mas probable
  predicted_winner_code TEXT,                  -- el codigo del equipo mas probable, NULL si empate mas probable
  predicted_scoreline   TEXT,                   -- "2-1", "1-0", etc

  -- Razones (top features que influyeron)
  reasons         JSONB,                       -- [{feature, value, contribution, label}]

  generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(match_id, model_version)
);

CREATE INDEX idx_wc_predictions_match ON wc_predictions(match_id);

-- =============================================================================
-- SIMULATIONS (Monte Carlo: P(campeon), P(final), P(semis), etc por equipo)
-- =============================================================================
CREATE TABLE IF NOT EXISTS wc_simulations (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  team_code       TEXT NOT NULL REFERENCES wc_teams(code) ON DELETE CASCADE,
  model_version   TEXT NOT NULL DEFAULT 'v1',
  n_simulations   INT NOT NULL,                -- 10000 tipicamente

  -- Probabilidades por fase alcanzada
  prob_winner          NUMERIC(5,4) NOT NULL,
  prob_finalist        NUMERIC(5,4) NOT NULL,
  prob_semifinal       NUMERIC(5,4) NOT NULL,
  prob_quarterfinal    NUMERIC(5,4) NOT NULL,
  prob_round_of_16     NUMERIC(5,4) NOT NULL,
  prob_round_of_32     NUMERIC(5,4) NOT NULL,
  prob_group_first     NUMERIC(5,4) NOT NULL,
  prob_group_second    NUMERIC(5,4) NOT NULL,
  prob_group_third     NUMERIC(5,4) NOT NULL,
  prob_eliminated_group NUMERIC(5,4) NOT NULL,

  -- Stats agregadas
  avg_goals_scored     NUMERIC(4,2),
  avg_goals_conceded   NUMERIC(4,2),

  generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(team_code, model_version)
);

CREATE INDEX idx_wc_simulations_winner ON wc_simulations(prob_winner DESC);

-- =============================================================================
-- ELO HISTORY (snapshot mensual del Elo de cada equipo)
-- =============================================================================
CREATE TABLE IF NOT EXISTS wc_elo_history (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  team_code       TEXT NOT NULL REFERENCES wc_teams(code) ON DELETE CASCADE,
  snapshot_date   DATE NOT NULL,
  elo_rating      NUMERIC NOT NULL,
  rank            INT,                          -- ranking entre las 48 selecciones
  UNIQUE(team_code, snapshot_date)
);

CREATE INDEX idx_wc_elo_history_team ON wc_elo_history(team_code, snapshot_date);

-- =============================================================================
-- HISTORICAL MATCHES (resultados internacionales para entrenar el modelo)
-- =============================================================================
CREATE TABLE IF NOT EXISTS wc_matches_historical (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  match_date      DATE NOT NULL,
  home_team       TEXT NOT NULL,
  away_team       TEXT NOT NULL,
  home_score      INT NOT NULL,
  away_score      INT NOT NULL,
  tournament      TEXT,
  city            TEXT,
  country         TEXT,
  neutral         BOOLEAN DEFAULT FALSE,
  importance      NUMERIC DEFAULT 1.0,         -- factor de importancia para Elo K
  imported_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_wc_hist_date ON wc_matches_historical(match_date DESC);
CREATE INDEX idx_wc_hist_home ON wc_matches_historical(home_team);
CREATE INDEX idx_wc_hist_away ON wc_matches_historical(away_team);

-- =============================================================================
-- RLS: lectura publica anon en todas las wc_* (uso interno, sin auth)
-- =============================================================================
DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'wc_teams','wc_players','wc_matches','wc_predictions',
    'wc_simulations','wc_elo_history','wc_matches_historical'
  ])
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', t);
    EXECUTE format('DROP POLICY IF EXISTS %I_select_all ON %I;', t, t);
    EXECUTE format('CREATE POLICY %I_select_all ON %I FOR SELECT TO anon, authenticated USING (true);', t, t);
  END LOOP;
END$$;

-- =============================================================================
-- VIEWS utilitarias
-- =============================================================================
CREATE OR REPLACE VIEW wc_v_top_favorites AS
SELECT
  t.code, t.name, t.flag_emoji, t.group_letter,
  t.elo_rating, t.fifa_rank,
  s.prob_winner, s.prob_finalist, s.prob_semifinal,
  s.prob_group_first, s.prob_eliminated_group
FROM wc_teams t
LEFT JOIN wc_simulations s ON s.team_code = t.code
ORDER BY s.prob_winner DESC NULLS LAST;

CREATE OR REPLACE VIEW wc_v_matches_with_predictions AS
SELECT
  m.id AS match_id, m.match_number, m.stage, m.group_letter,
  m.scheduled_at, m.venue_city, m.venue_stadium, m.venue_country,
  m.home_team_code, m.away_team_code, m.home_label, m.away_label,
  m.home_score, m.away_score, m.status,
  th.name AS home_name, th.flag_emoji AS home_flag,
  ta.name AS away_name, ta.flag_emoji AS away_flag,
  p.prob_home_win, p.prob_draw, p.prob_away_win,
  p.expected_home_goals, p.expected_away_goals,
  p.predicted_winner_code, p.predicted_scoreline,
  p.reasons
FROM wc_matches m
LEFT JOIN wc_teams th ON th.code = m.home_team_code
LEFT JOIN wc_teams ta ON ta.code = m.away_team_code
LEFT JOIN wc_predictions p ON p.match_id = m.id
ORDER BY m.match_number;

GRANT SELECT ON wc_v_top_favorites TO anon, authenticated;
GRANT SELECT ON wc_v_matches_with_predictions TO anon, authenticated;
