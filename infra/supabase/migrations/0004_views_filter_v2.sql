-- =============================================================================
-- Fix: las vistas no filtraban por model_version. Como ahora hay v1 + v2,
-- cada equipo/partido aparecía duplicado en /, /bracket y /matches.
-- Filtramos por v2 (modelo de producción).
-- =============================================================================

DROP VIEW IF EXISTS wc_v_top_favorites CASCADE;
DROP VIEW IF EXISTS wc_v_matches_with_predictions CASCADE;
DROP VIEW IF EXISTS wc_v_podium CASCADE;

CREATE OR REPLACE VIEW wc_v_top_favorites AS
SELECT
  t.code, t.name, t.flag_emoji, t.group_letter,
  t.elo_rating, t.fifa_rank, t.confederation, t.is_host,
  s.prob_winner,
  s.prob_finalist,
  s.prob_semifinal,
  s.prob_quarterfinal,
  s.prob_round_of_16,
  s.prob_round_of_32,
  s.prob_group_first,
  s.prob_group_second,
  s.prob_group_third,
  s.prob_eliminated_group,
  s.avg_goals_scored,
  s.avg_goals_conceded,
  s.n_simulations
FROM wc_teams t
LEFT JOIN wc_simulations s
  ON s.team_code = t.code AND s.model_version = 'v2'
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
LEFT JOIN wc_predictions p
  ON p.match_id = m.id AND p.model_version = 'v2'
ORDER BY m.match_number;

CREATE OR REPLACE VIEW wc_v_podium AS
SELECT
  t.code, t.name, t.flag_emoji, t.confederation, t.group_letter, t.elo_rating,
  o.prob_champion, o.prob_runner_up, o.prob_third, o.prob_fourth, o.prob_podium,
  s.prob_winner, s.prob_finalist, s.prob_semifinal, s.prob_quarterfinal, s.prob_round_of_16
FROM wc_teams t
LEFT JOIN wc_tournament_outcomes o
  ON o.team_code = t.code AND o.model_version = 'v2'
LEFT JOIN wc_simulations s
  ON s.team_code = t.code AND s.model_version = 'v2'
ORDER BY o.prob_champion DESC NULLS LAST;

GRANT SELECT ON wc_v_top_favorites TO anon, authenticated;
GRANT SELECT ON wc_v_matches_with_predictions TO anon, authenticated;
GRANT SELECT ON wc_v_podium TO anon, authenticated;
