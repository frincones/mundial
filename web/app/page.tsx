import Link from "next/link";
import { fetchTeams, fetchSimulations, fetchPodium, fetchTopScorers } from "@/lib/supabase";
import { TeamBadge } from "@/components/TeamBadge";
import { fmtPct, daysToKickoff } from "@/lib/format";
import { Trophy, Calendar, GitBranch, Sparkles, Target, Award, Medal } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const [teams, sims, podium, scorers] = await Promise.all([
    fetchTeams(),
    fetchSimulations(),
    fetchPodium(),
    fetchTopScorers(),
  ]);
  const byCode = new Map(teams.map((t) => [t.code, t]));
  const top = sims.slice(0, 10);

  const champion = [...podium].sort((a, b) => (b.prob_champion ?? 0) - (a.prob_champion ?? 0))[0];
  const runnerUp = [...podium].sort((a, b) => (b.prob_runner_up ?? 0) - (a.prob_runner_up ?? 0))[0];
  const third = [...podium].sort((a, b) => (b.prob_third ?? 0) - (a.prob_third ?? 0))[0];
  const fourth = [...podium].sort((a, b) => (b.prob_fourth ?? 0) - (a.prob_fourth ?? 0))[0];
  const topScorer = scorers[0];
  const championTeam = champion ? byCode.get(champion.code) : undefined;
  const days = daysToKickoff();

  return (
    <div className="space-y-10">
      {/* Hero */}
      <section className="text-center py-10">
        <p className="text-wc-600 text-sm font-semibold uppercase tracking-wider mb-2">
          Mundial FIFA 2026 — USA · Canadá · México
        </p>
        <h1 className="text-5xl sm:text-6xl font-bold text-slate-900 mb-4">
          ¿Quién va a ser el <span className="text-wc-600">campeón</span>?
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-6">
          Predicciones ML basadas en 49.257 partidos internacionales, Elo ratings actualizados y 200.000 simulaciones Monte Carlo con ensemble de 5 modelos.
        </p>
        <div className="inline-flex items-center gap-3 bg-white border border-slate-200 rounded-full px-5 py-2 shadow-sm">
          <Calendar size={16} className="text-wc-600" />
          <span className="font-semibold text-slate-900">
            {days > 0 ? `Faltan ${days} días para el kickoff` : "¡El Mundial ya empezó!"}
          </span>
          <span className="text-xs text-slate-400">· 11 jun 2026, MEX vs RSA</span>
        </div>
      </section>

      {/* Campeón predicho */}
      {championTeam && champion && (
        <section className="card p-8 border-l-4 border-l-wcgold-500 bg-gradient-to-br from-wcgold-50 to-white">
          <div className="flex items-center gap-2 mb-3 text-wcgold-600">
            <Trophy size={20} />
            <span className="text-sm font-semibold uppercase tracking-wider">🏆 Campeón del Mundo 2026</span>
          </div>
          <div className="flex items-center gap-6 flex-wrap">
            <span className="text-7xl">{championTeam.flag_emoji}</span>
            <div className="flex-1 min-w-[280px]">
              <h2 className="text-3xl font-bold text-slate-900 mb-1">{championTeam.name}</h2>
              <p className="text-slate-600 text-sm mb-3">
                Grupo {championTeam.group_letter} · Elo {Math.round(championTeam.elo_rating)} · FIFA #{championTeam.fifa_rank}
              </p>
              <div className="grid grid-cols-4 gap-3 text-sm">
                <Stat label="Campeón" value={fmtPct(champion.prob_champion ?? 0)} hot />
                <Stat label="Finalista" value={fmtPct(champion.prob_finalist ?? 0)} />
                <Stat label="Podio" value={fmtPct(champion.prob_podium ?? 0)} />
                <Stat label="Semifinal" value={fmtPct(champion.prob_semifinal ?? 0)} />
              </div>
              <Link
                href="/podium"
                className="inline-flex items-center gap-1.5 mt-4 text-sm font-medium text-wcgold-700 hover:text-wcgold-800"
              >
                Ver podio completo <Award size={14} />
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* Podio 2-3-4 + Bota de Oro */}
      <section className="grid md:grid-cols-4 gap-4">
        <PodiumMini
          medal="🥈" label="Subcampeón" color="border-l-slate-400"
          team={byCode.get(runnerUp?.code)} prob={runnerUp?.prob_runner_up}
        />
        <PodiumMini
          medal="🥉" label="Tercer puesto" color="border-l-amber-700"
          team={byCode.get(third?.code)} prob={third?.prob_third}
        />
        <PodiumMini
          medal="4°" label="Cuarto lugar" color="border-l-slate-300"
          team={byCode.get(fourth?.code)} prob={fourth?.prob_fourth}
        />
        {topScorer && (
          <div className="card p-5 border-l-4 border-l-wc-500 text-center bg-gradient-to-br from-wc-50 to-white">
            <div className="text-xl mb-1">⚽</div>
            <p className="text-xs uppercase text-slate-500 tracking-wider mb-3">Bota de Oro</p>
            <div className="text-4xl mb-2">{byCode.get(topScorer.team_code)?.flag_emoji}</div>
            <p className="font-bold text-slate-900 text-sm leading-tight">{topScorer.player_name}</p>
            <p className="text-xs text-slate-500 mt-1">{byCode.get(topScorer.team_code)?.name}</p>
            <p className="text-2xl font-bold text-wc-700 mt-2">
              {Number(topScorer.predicted_goals).toFixed(1)}
              <span className="text-xs font-normal text-slate-500"> goles esp.</span>
            </p>
            <p className="text-xs text-slate-500">{fmtPct(topScorer.prob_top_scorer ?? 0)} P(Bota Oro)</p>
          </div>
        )}
      </section>

      {/* Top 10 favoritos */}
      <section>
        <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Sparkles className="text-wc-600" size={22} /> Top 10 favoritos al título
        </h2>
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr className="text-left text-xs uppercase text-slate-500 tracking-wider">
                <th className="px-4 py-3 w-12">#</th>
                <th className="px-4 py-3">Equipo</th>
                <th className="px-4 py-3">Grupo</th>
                <th className="px-4 py-3 text-right">Elo</th>
                <th className="px-4 py-3 text-right">P(Campeón)</th>
                <th className="px-4 py-3 text-right">P(Final)</th>
                <th className="px-4 py-3 text-right">P(Semifinal)</th>
              </tr>
            </thead>
            <tbody>
              {top.map((s, i) => {
                const t = teams.find((x) => x.code === s.code);
                return (
                  <tr key={s.code} className="border-b border-slate-100 hover:bg-wc-50/50 transition-colors">
                    <td className="px-4 py-3 text-slate-400 font-mono">{i + 1}</td>
                    <td className="px-4 py-3">
                      <TeamBadge team={t} size="md" />
                    </td>
                    <td className="px-4 py-3 text-slate-600">{t?.group_letter}</td>
                    <td className="px-4 py-3 text-right font-mono text-slate-700">
                      {Math.round(t?.elo_rating || 0)}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-wc-700">
                      {fmtPct(s.prob_winner)}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600">{fmtPct(s.prob_finalist)}</td>
                    <td className="px-4 py-3 text-right text-slate-600">{fmtPct(s.prob_semifinal)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-400 text-center mt-2">
          Basado en 200.000 simulaciones Monte Carlo · ensemble v2 (5 modelos) · Elo + Poisson bivariado + form histórico
        </p>
      </section>

      {/* Navegación */}
      <section className="grid md:grid-cols-4 gap-4">
        <Link href="/podium" className="card p-6 hover:shadow-md transition-shadow">
          <Award className="text-wcgold-600 mb-2" size={24} />
          <h3 className="font-semibold text-slate-900 mb-1">Podio + Bota Oro</h3>
          <p className="text-sm text-slate-500">Top 12 podio y top 20 goleadores con probabilidades</p>
        </Link>
        <Link href="/matches" className="card p-6 hover:shadow-md transition-shadow">
          <Calendar className="text-wc-600 mb-2" size={24} />
          <h3 className="font-semibold text-slate-900 mb-1">104 partidos</h3>
          <p className="text-sm text-slate-500">Probabilidades W/D/L + xG por cada partido del torneo</p>
        </Link>
        <Link href="/bracket" className="card p-6 hover:shadow-md transition-shadow">
          <GitBranch className="text-wc-600 mb-2" size={24} />
          <h3 className="font-semibold text-slate-900 mb-1">Bracket</h3>
          <p className="text-sm text-slate-500">Eliminatoria proyectada con probabilidades por nodo</p>
        </Link>
        <Link href="/teams" className="card p-6 hover:shadow-md transition-shadow">
          <Trophy className="text-wc-600 mb-2" size={24} />
          <h3 className="font-semibold text-slate-900 mb-1">48 equipos</h3>
          <p className="text-sm text-slate-500">Perfil completo de cada selección con stats Monte Carlo</p>
        </Link>
      </section>
    </div>
  );
}

function Stat({ label, value, hot }: { label: string; value: string; hot?: boolean }) {
  return (
    <div className={`p-3 rounded-md ${hot ? "bg-wcgold-100" : "bg-white border border-slate-200"}`}>
      <p className="text-xs text-slate-500 uppercase">{label}</p>
      <p className={`text-xl font-bold ${hot ? "text-wcgold-700" : "text-slate-900"}`}>{value}</p>
    </div>
  );
}

function PodiumMini({ medal, label, color, team, prob }: any) {
  if (!team) return null;
  return (
    <div className={`card p-5 border-l-4 ${color} text-center`}>
      <div className="text-xl mb-1">{medal}</div>
      <p className="text-xs uppercase text-slate-500 tracking-wider mb-3">{label}</p>
      <div className="text-4xl mb-2">{team.flag_emoji}</div>
      <p className="font-bold text-slate-900 text-sm">{team.name}</p>
      <p className="text-2xl font-bold text-slate-700 mt-2">{fmtPct(prob ?? 0)}</p>
    </div>
  );
}
