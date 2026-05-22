import { fetchPodium, fetchTopScorers, fetchTeams } from "@/lib/supabase";
import { TeamBadge } from "@/components/TeamBadge";
import { fmtPct } from "@/lib/format";
import { Trophy, Medal, Award, Target } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function PodiumPage() {
  const [podium, scorers, teams] = await Promise.all([
    fetchPodium(),
    fetchTopScorers(),
    fetchTeams(),
  ]);
  const byCode = new Map(teams.map((t) => [t.code, t]));

  // Top de cada posición
  const champion = [...podium].sort((a, b) => (b.prob_champion ?? 0) - (a.prob_champion ?? 0))[0];
  const runnerUp = [...podium].sort((a, b) => (b.prob_runner_up ?? 0) - (a.prob_runner_up ?? 0))[0];
  const third = [...podium].sort((a, b) => (b.prob_third ?? 0) - (a.prob_third ?? 0))[0];
  const fourth = [...podium].sort((a, b) => (b.prob_fourth ?? 0) - (a.prob_fourth ?? 0))[0];
  const topScorer = scorers[0];

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
          <Trophy className="text-wcgold-600" /> Podio predicho
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Resultados según 200.000 simulaciones Monte Carlo del torneo completo · ensemble de 5 modelos
        </p>
      </header>

      {/* Hero — Campeón */}
      {champion && (
        <section className="card p-10 bg-gradient-to-br from-wcgold-50 via-white to-wc-50 border-l-8 border-l-wcgold-500">
          <div className="flex items-center gap-2 mb-3 text-wcgold-600">
            <Trophy size={20} />
            <span className="text-xs font-semibold uppercase tracking-widest">🏆 Campeón del Mundo 2026</span>
          </div>
          <div className="flex items-center gap-8 flex-wrap">
            <span className="text-9xl">{byCode.get(champion.code)?.flag_emoji}</span>
            <div className="flex-1">
              <h2 className="text-5xl font-bold text-slate-900">{champion.name}</h2>
              <p className="text-slate-600 mt-2">Grupo {champion.group_letter} · Elo {Math.round(champion.elo_rating || 0)}</p>
              <p className="mt-4 text-7xl font-bold text-wcgold-600">
                {fmtPct(champion.prob_champion ?? 0)}
              </p>
              <p className="text-xs text-slate-500 mt-2">Probabilidad de ganar el torneo</p>
            </div>
          </div>
        </section>
      )}

      {/* Top 3 + 4to */}
      <section className="grid md:grid-cols-3 gap-4">
        <PodiumCard
          rank={2} medal="🥈" color="border-l-slate-400"
          team={byCode.get(runnerUp.code)} prob={runnerUp.prob_runner_up} label="Subcampeón"
        />
        <PodiumCard
          rank={3} medal="🥉" color="border-l-amber-700"
          team={byCode.get(third.code)} prob={third.prob_third} label="Tercer puesto"
        />
        <PodiumCard
          rank={4} medal="4°" color="border-l-slate-300"
          team={byCode.get(fourth.code)} prob={fourth.prob_fourth} label="Cuarto lugar"
        />
      </section>

      {/* Bota de Oro */}
      {topScorer && (
        <section className="card p-8 border-l-4 border-l-wc-500 bg-gradient-to-br from-wc-50 to-white">
          <div className="flex items-center gap-2 mb-3 text-wc-600">
            <Target size={20} />
            <span className="text-xs font-semibold uppercase tracking-widest">⚽ Bota de Oro — Máximo goleador</span>
          </div>
          <div className="flex items-center gap-6 flex-wrap">
            <span className="text-7xl">{byCode.get(topScorer.team_code)?.flag_emoji}</span>
            <div className="flex-1">
              <h2 className="text-3xl font-bold text-slate-900">{topScorer.player_name}</h2>
              <p className="text-slate-600 mt-1">
                {byCode.get(topScorer.team_code)?.name} · {topScorer.position}
              </p>
              <div className="grid grid-cols-3 gap-3 mt-4 max-w-md">
                <Stat label="Goles esperados" value={topScorer.predicted_goals.toFixed(2)} hot />
                <Stat label="P(Bota Oro)" value={fmtPct(topScorer.prob_top_scorer)} />
                <Stat label="P(5+ goles)" value={fmtPct(topScorer.prob_5_plus)} />
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Tabla podio top 12 */}
      <section className="card overflow-hidden">
        <div className="p-4 border-b border-slate-200">
          <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <Medal size={16} className="text-wcgold-600" /> Top 12 — Probabilidades del podio
          </h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr className="text-xs uppercase text-slate-500">
              <th className="px-4 py-3 text-left">#</th>
              <th className="px-4 py-3 text-left">Equipo</th>
              <th className="px-4 py-3 text-right">🏆 Camp.</th>
              <th className="px-4 py-3 text-right">🥈 2do</th>
              <th className="px-4 py-3 text-right">🥉 3ro</th>
              <th className="px-4 py-3 text-right">4to</th>
              <th className="px-4 py-3 text-right">Podio total</th>
            </tr>
          </thead>
          <tbody>
            {podium.slice(0, 12).map((p, i) => (
              <tr key={p.code} className="border-t border-slate-100 hover:bg-wc-50/30">
                <td className="px-4 py-2 text-slate-400 font-mono">{i + 1}</td>
                <td className="px-4 py-2"><TeamBadge team={byCode.get(p.code)} size="md" /></td>
                <td className="px-4 py-2 text-right font-semibold text-wcgold-700">{fmtPct(p.prob_champion ?? 0)}</td>
                <td className="px-4 py-2 text-right">{fmtPct(p.prob_runner_up ?? 0)}</td>
                <td className="px-4 py-2 text-right">{fmtPct(p.prob_third ?? 0)}</td>
                <td className="px-4 py-2 text-right text-slate-500">{fmtPct(p.prob_fourth ?? 0)}</td>
                <td className="px-4 py-2 text-right font-medium text-slate-700">{fmtPct(p.prob_podium ?? 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Top 20 goleadores */}
      <section className="card overflow-hidden">
        <div className="p-4 border-b border-slate-200">
          <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <Target size={16} className="text-wc-600" /> Top 20 candidatos a Bota de Oro
          </h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr className="text-xs uppercase text-slate-500">
              <th className="px-4 py-3 text-left">#</th>
              <th className="px-4 py-3 text-left">Jugador</th>
              <th className="px-4 py-3 text-left">Selección</th>
              <th className="px-4 py-3 text-left">Pos</th>
              <th className="px-4 py-3 text-right">Goles esperados</th>
              <th className="px-4 py-3 text-right">P(Bota Oro)</th>
              <th className="px-4 py-3 text-right">P(5+)</th>
            </tr>
          </thead>
          <tbody>
            {scorers.slice(0, 20).map((s, i) => (
              <tr key={`${s.player_name}-${s.team_code}`} className="border-t border-slate-100 hover:bg-wc-50/30">
                <td className="px-4 py-2 text-slate-400 font-mono">{i + 1}</td>
                <td className="px-4 py-2 font-medium text-slate-900">{s.player_name}</td>
                <td className="px-4 py-2">
                  <TeamBadge team={byCode.get(s.team_code)} size="md" />
                </td>
                <td className="px-4 py-2 text-xs text-slate-500">{s.position}</td>
                <td className="px-4 py-2 text-right font-semibold text-wc-700">{Number(s.predicted_goals).toFixed(2)}</td>
                <td className="px-4 py-2 text-right">{fmtPct(s.prob_top_scorer ?? 0)}</td>
                <td className="px-4 py-2 text-right text-slate-500">{fmtPct(s.prob_5_plus ?? 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function PodiumCard({ rank, medal, color, team, prob, label }: any) {
  if (!team) return null;
  return (
    <div className={`card p-6 border-l-4 ${color} text-center`}>
      <div className="text-3xl mb-1">{medal}</div>
      <p className="text-xs uppercase text-slate-500 tracking-wider mb-3">{label}</p>
      <div className="text-5xl mb-2">{team.flag_emoji}</div>
      <p className="font-bold text-slate-900">{team.name}</p>
      <p className="text-2xl font-bold text-slate-700 mt-2">{fmtPct(prob ?? 0)}</p>
    </div>
  );
}

function Stat({ label, value, hot }: any) {
  return (
    <div className={`p-3 rounded-md ${hot ? "bg-wc-100" : "bg-white border border-slate-200"}`}>
      <p className="text-xs text-slate-500 uppercase">{label}</p>
      <p className={`text-xl font-bold ${hot ? "text-wc-700" : "text-slate-900"}`}>{value}</p>
    </div>
  );
}
