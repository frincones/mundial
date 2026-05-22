-- =============================================================================
-- Fix: vista wc_v_top_favorites le faltaban columnas de Octavos y Cuartos
-- =============================================================================

DROP VIEW IF EXISTS wc_v_top_favorites CASCADE;

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
LEFT JOIN wc_simulations s ON s.team_code = t.code
ORDER BY s.prob_winner DESC NULLS LAST;

GRANT SELECT ON wc_v_top_favorites TO anon, authenticated;
