import Link from "next/link";
import { fetchTeams, fetchSimulations } from "@/lib/supabase";
import { TeamBadge } from "@/components/TeamBadge";
import { fmtPct, daysToKickoff } from "@/lib/format";
import { Trophy, Calendar, GitBranch, Sparkles } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const [teams, sims] = await Promise.all([fetchTeams(), fetchSimulations()]);
  const top = sims.slice(0, 10);
  const champion = top[0];
  const championTeam = teams.find((t) => t.code === champion?.code);
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
          Predicciones ML basadas en 49.257 partidos internacionales, Elo ratings actualizados y 10.000 simulaciones Monte Carlo.
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
      {championTeam && (
        <section className="card p-8 border-l-4 border-l-wcgold-500 bg-gradient-to-br from-wcgold-50 to-white">
          <div className="flex items-center gap-2 mb-3 text-wcgold-600">
            <Trophy size={20} />
            <span className="text-sm font-semibold uppercase tracking-wider">Predicción del campeón</span>
          </div>
          <div className="flex items-center gap-6">
            <span className="text-7xl">{championTeam.flag_emoji}</span>
            <div className="flex-1">
              <h2 className="text-3xl font-bold text-slate-900 mb-1">{championTeam.name}</h2>
              <p className="text-slate-600 text-sm mb-3">
                Grupo {championTeam.group_letter} · Elo {Math.round(championTeam.elo_rating)} · FIFA #{championTeam.fifa_rank}
              </p>
              <div className="grid grid-cols-4 gap-3 text-sm">
                <Stat label="Campeón" value={fmtPct(champion.prob_winner)} hot />
                <Stat label="Finalista" value={fmtPct(champion.prob_finalist)} />
                <Stat label="Semifinal" value={fmtPct(champion.prob_semifinal)} />
                <Stat label="Cuartos" value={fmtPct(champion.prob_quarterfinal)} />
              </div>
            </div>
          </div>
        </section>
      )}

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
          Basado en 10.000 simulaciones Monte Carlo del torneo completo · Modelo Elo + Poisson
        </p>
      </section>

      {/* Navegación */}
      <section className="grid md:grid-cols-3 gap-4">
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
