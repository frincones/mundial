import Link from "next/link";
import { notFound } from "next/navigation";
import { fetchTeamByCode, fetchTeamSimulation, fetchTeamMatches } from "@/lib/supabase";
import { TeamBadge } from "@/components/TeamBadge";
import { MatchCard } from "@/components/MatchCard";
import { fmtPct, confLabel } from "@/lib/format";
import { ArrowLeft, Trophy, TrendingUp, Award, Users } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function TeamDetailPage({ params }: { params: { code: string } }) {
  const code = params.code.toUpperCase();
  const [team, sim, teamMatches] = await Promise.all([
    fetchTeamByCode(code),
    fetchTeamSimulation(code),
    fetchTeamMatches(code),
  ]);
  if (!team) notFound();

  return (
    <div className="space-y-6">
      <Link href="/teams" className="text-sm text-slate-500 hover:text-wc-700 inline-flex items-center gap-1">
        <ArrowLeft size={14} /> Volver a equipos
      </Link>

      {/* Hero */}
      <section className="card p-8 bg-gradient-to-br from-wc-50 via-white to-wcgold-50">
        <div className="flex items-start justify-between gap-6 flex-wrap">
          <div className="flex items-center gap-5">
            <span className="text-7xl">{team.flag_emoji}</span>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">{team.name}</h1>
              <p className="text-slate-600 mt-1 text-sm">
                {confLabel(team.confederation)} · Grupo {team.group_letter}
                {team.is_host && " · 🏟️ Anfitrión"}
                {team.is_debut && " · ⭐ Debut"}
              </p>
              <p className="text-xs text-slate-500 mt-1">DT: {team.manager_name || "—"}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-white border border-slate-200 rounded-md p-3 text-center">
              <p className="text-xs text-slate-500 uppercase">Elo</p>
              <p className="text-2xl font-bold text-slate-900">{Math.round(team.elo_rating)}</p>
            </div>
            <div className="bg-white border border-slate-200 rounded-md p-3 text-center">
              <p className="text-xs text-slate-500 uppercase">FIFA Rank</p>
              <p className="text-2xl font-bold text-slate-900">#{team.fifa_rank || "—"}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Probabilidades */}
      {sim && (
        <section className="card p-6">
          <h2 className="text-sm font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <TrendingUp size={16} className="text-wc-600" />
            Probabilidades del torneo (100K simulaciones Monte Carlo)
          </h2>
          <div className="grid md:grid-cols-5 gap-3 mb-4">
            <ProbBox label="🏆 Campeón" value={fmtPct(sim.prob_winner)} hot />
            <ProbBox label="Finalista" value={fmtPct(sim.prob_finalist)} />
            <ProbBox label="Semifinal" value={fmtPct(sim.prob_semifinal)} />
            <ProbBox label="Cuartos" value={fmtPct(sim.prob_quarterfinal)} />
            <ProbBox label="Octavos" value={fmtPct(sim.prob_round_of_16)} />
          </div>
          <div className="border-t border-slate-200 pt-4">
            <p className="text-xs uppercase text-slate-500 mb-3">Resultado en fase de grupos</p>
            <div className="grid md:grid-cols-4 gap-3">
              <ProbBox label="1° del grupo" value={fmtPct(sim.prob_group_first)} />
              <ProbBox label="2° del grupo" value={fmtPct(sim.prob_group_second)} />
              <ProbBox label="3° del grupo" value={fmtPct(sim.prob_group_third)} />
              <ProbBox label="Eliminado" value={fmtPct(sim.prob_eliminated_group)} negative />
            </div>
          </div>
          <div className="border-t border-slate-200 pt-4 mt-4 grid md:grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-xs text-slate-500 uppercase">Goles esperados a favor</p>
              <p className="text-xl font-bold text-emerald-700">{sim.avg_goals_scored.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase">Goles esperados en contra</p>
              <p className="text-xl font-bold text-rose-700">{sim.avg_goals_conceded.toFixed(2)}</p>
            </div>
          </div>
        </section>
      )}

      {/* Partidos del equipo */}
      <section>
        <h2 className="text-sm font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Award size={16} className="text-wc-600" />
          Partidos del torneo
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          {teamMatches.map((m: any) => (
            <MatchCard key={m.match_id} match={m} />
          ))}
        </div>
      </section>
    </div>
  );
}

function ProbBox({ label, value, hot, negative }: any) {
  const cls = hot
    ? "bg-wcgold-100 text-wcgold-700 border-wcgold-300"
    : negative
    ? "bg-rose-50 text-rose-700 border-rose-200"
    : "bg-slate-50 text-slate-700 border-slate-200";
  return (
    <div className={`border rounded-md p-3 text-center ${cls}`}>
      <p className="text-xs uppercase opacity-70">{label}</p>
      <p className="text-xl font-bold mt-1">{value}</p>
    </div>
  );
}
