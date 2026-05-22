import Link from "next/link";
import { fetchTeams, fetchSimulations } from "@/lib/supabase";
import { TeamBadge } from "@/components/TeamBadge";
import { fmtPct, confLabel } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function TeamsPage() {
  const [teams, sims] = await Promise.all([fetchTeams(), fetchSimulations()]);
  const simByCode = new Map(sims.map((s) => [s.code, s]));

  const groups: Record<string, any[]> = {};
  for (const t of teams) {
    if (!groups[t.group_letter]) groups[t.group_letter] = [];
    groups[t.group_letter].push(t);
  }
  for (const g of Object.keys(groups)) {
    groups[g].sort((a, b) => a.group_position - b.group_position);
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-slate-900 mb-1">48 selecciones · 12 grupos</h1>
        <p className="text-sm text-slate-500">
          Cada equipo con su probabilidad de avanzar a cada fase según el modelo
        </p>
      </header>

      <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-5">
        {Object.entries(groups).map(([letter, gteams]) => (
          <div key={letter} className="card p-4">
            <h2 className="font-semibold text-slate-900 mb-3 flex items-center justify-between">
              <span>Grupo {letter}</span>
              <span className="text-xs text-slate-400">{gteams[0].venue_city || ""}</span>
            </h2>
            <div className="space-y-2">
              {gteams.map((t) => {
                const s = simByCode.get(t.code);
                return (
                  <Link
                    key={t.code}
                    href={`/teams/${t.code}`}
                    className="flex items-center gap-2 p-2 rounded hover:bg-wc-50 transition-colors"
                  >
                    <span className="text-xl">{t.flag_emoji}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{t.name}</p>
                      <p className="text-xs text-slate-500">{confLabel(t.confederation)} · Elo {Math.round(t.elo_rating)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-slate-400">Camp.</p>
                      <p className="text-sm font-semibold text-wc-700">
                        {s ? fmtPct(s.prob_winner) : "—"}
                      </p>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
