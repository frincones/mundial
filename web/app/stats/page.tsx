import { fetchTeams, fetchSimulations } from "@/lib/supabase";
import { StatsCharts } from "./StatsCharts";

export const dynamic = "force-dynamic";

export default async function StatsPage() {
  const [teams, sims] = await Promise.all([fetchTeams(), fetchSimulations()]);
  return <StatsCharts teams={teams} sims={sims} />;
}
