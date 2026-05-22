// Helpers de data — leen los JSON estaticos servidos en /public/data

import teamsJson from "@/public/data/teams.json";
import matchesJson from "@/public/data/matches.json";
import predictionsJson from "@/public/data/predictions.json";
import simulationsJson from "@/public/data/simulations.json";

export type Team = {
  code: string;
  name: string;
  flag_emoji: string;
  confederation: string;
  group_letter: string;
  group_position: number;
  is_host: boolean;
  fifa_rank: number | null;
  elo_rating: number;
  manager_name: string | null;
  is_debut: boolean;
};

export type Match = {
  match_number: number;
  stage: string;
  group_letter: string | null;
  scheduled_at: string;
  venue_city: string;
  venue_stadium: string;
  venue_country: string;
  home_team_code: string | null;
  away_team_code: string | null;
  home_label: string | null;
  away_label: string | null;
  home_score: number | null;
  away_score: number | null;
  status: string;
};

export type Prediction = {
  match_number: number;
  stage: string;
  home_team_code: string;
  away_team_code: string;
  prob_home_win: number;
  prob_draw: number;
  prob_away_win: number;
  expected_home_goals: number;
  expected_away_goals: number;
  predicted_winner_code: string | null;
  predicted_scoreline: string;
  reasons: Array<{ feature: string; value: number; contribution: number; label: string }>;
};

export type Simulation = {
  team_code: string;
  n_simulations: number;
  prob_winner: number;
  prob_finalist: number;
  prob_semifinal: number;
  prob_quarterfinal: number;
  prob_round_of_16: number;
  prob_round_of_32: number;
  prob_group_first: number;
  prob_group_second: number;
  prob_group_third: number;
  prob_eliminated_group: number;
  avg_goals_scored: number;
  avg_goals_conceded: number;
};

export const teams: Team[] = teamsJson as Team[];
export const matches: Match[] = matchesJson as Match[];
export const predictions: Prediction[] = predictionsJson as Prediction[];
export const simulations: Simulation[] = simulationsJson as Simulation[];

// Lookups
export const teamByCode = (code: string | null): Team | undefined =>
  code ? teams.find((t) => t.code === code) : undefined;

export const predictionByMatchNumber = (n: number): Prediction | undefined =>
  predictions.find((p) => p.match_number === n);

export const simulationByCode = (code: string): Simulation | undefined =>
  simulations.find((s) => s.team_code === code);

export const teamsByGroup = (): Record<string, Team[]> => {
  const map: Record<string, Team[]> = {};
  for (const t of teams) {
    if (!map[t.group_letter]) map[t.group_letter] = [];
    map[t.group_letter].push(t);
  }
  for (const g of Object.keys(map)) {
    map[g].sort((a, b) => a.group_position - b.group_position);
  }
  return map;
};

export const topFavorites = (n: number = 10): Simulation[] => {
  return [...simulations].sort((a, b) => b.prob_winner - a.prob_winner).slice(0, n);
};

export const champion = (): { team: Team; sim: Simulation } | null => {
  const top = simulations.sort((a, b) => b.prob_winner - a.prob_winner)[0];
  if (!top) return null;
  const t = teamByCode(top.team_code);
  return t ? { team: t, sim: top } : null;
};

export const stageLabel = (stage: string): string =>
  ({
    group: "Fase de grupos",
    r32: "Ronda de 32",
    r16: "Octavos de final",
    qf: "Cuartos de final",
    sf: "Semifinales",
    "3rd": "Tercer puesto",
    final: "Final",
  } as Record<string, string>)[stage] || stage;

export const formatDate = (iso: string): string => {
  const d = new Date(iso);
  return d.toLocaleString("es-CO", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/Bogota",
  });
};

export const daysToKickoff = (): number => {
  const kickoff = new Date("2026-06-11T18:00:00Z");
  const diff = kickoff.getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
};

export const totalMatches = matches.length;
export const groupMatchesCount = matches.filter((m) => m.stage === "group").length;
export const knockoutMatchesCount = totalMatches - groupMatchesCount;
