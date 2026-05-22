// Cliente Supabase para leer wc_* desde el frontend (server components)
// Lee via REST con anon key porque RLS permite SELECT publico.

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const SUPABASE_ANON = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

async function rest<T = any>(path: string): Promise<T> {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    headers: { apikey: SUPABASE_ANON, Authorization: `Bearer ${SUPABASE_ANON}` },
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`Supabase ${r.status}: ${await r.text()}`);
  return r.json();
}

export const fetchTeams = () =>
  rest<any[]>("wc_teams?select=*&order=group_letter,group_position");

export const fetchMatches = () =>
  rest<any[]>("wc_v_matches_with_predictions?select=*&order=match_number");

export const fetchSimulations = () =>
  rest<any[]>("wc_v_top_favorites?select=*");

export const fetchTeamByCode = (code: string) =>
  rest<any[]>(`wc_teams?code=eq.${code}&select=*&limit=1`).then((rs) => rs[0] ?? null);

export const fetchTeamSimulation = (code: string) =>
  rest<any[]>(`wc_simulations?team_code=eq.${code}&select=*&limit=1`).then((rs) => rs[0] ?? null);

export const fetchTeamMatches = (code: string) =>
  rest<any[]>(
    `wc_v_matches_with_predictions?or=(home_team_code.eq.${code},away_team_code.eq.${code})&order=match_number`
  );

export const fetchPodium = () =>
  rest<any[]>("wc_v_podium?select=*");

export const fetchTopScorers = () =>
  rest<any[]>("wc_top_scorers?model_version=eq.v2&order=predicted_goals.desc&limit=30");

export const fetchPlayers = (teamCode: string) =>
  rest<any[]>(`wc_players?team_code=eq.${teamCode}&select=*&order=jersey_number`);
