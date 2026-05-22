import { fetchMatches } from "@/lib/supabase";
import { MatchesGrid } from "./MatchesGrid";

export const dynamic = "force-dynamic";

export default async function MatchesPage() {
  const matches = await fetchMatches();
  return <MatchesGrid matches={matches} />;
}
