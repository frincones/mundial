import { fetchTeams, fetchSimulations } from "@/lib/supabase";
import { TeamBadge } from "@/components/TeamBadge";
import { fmtPct } from "@/lib/format";
import { Trophy, GitBranch } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function BracketPage() {
  const [teams, sims] = await Promise.all([fetchTeams(), fetchSimulations()]);
  const teamByCode = new Map(teams.map((t) => [t.code, t]));
  const simByCode = new Map(sims.map((s) => [s.code, s]));

  // Construir bracket proyectado: top picks por fase
  const sortedByWinner = [...sims].sort((a, b) => b.prob_winner - a.prob_winner);
  const top32 = [...sims].sort((a, b) => b.prob_round_of_16 - a.prob_round_of_16).slice(0, 32);
  const top16 = [...sims].sort((a, b) => b.prob_round_of_16 - a.prob_round_of_16).slice(0, 16);
  const top8 = [...sims].sort((a, b) => b.prob_quarterfinal - a.prob_quarterfinal).slice(0, 8);
  const top4 = [...sims].sort((a, b) => b.prob_semifinal - a.prob_semifinal).slice(0, 4);
  const top2 = [...sims].sort((a, b) => b.prob_finalist - a.prob_finalist).slice(0, 2);
  const champion = sortedByWinner[0];

  const rowFor = (s: any) => {
    const t = teamByCode.get(s.code);
    return (
      <div key={s.code} className="flex items-center justify-between bg-white border border-slate-200 rounded-md px-3 py-2 hover:border-wc-300 transition-colors">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-lg">{t?.flag_emoji}</span>
          <span className="text-sm font-medium truncate">{t?.name}</span>
        </div>
        <span className="text-xs text-wc-700 font-semibold ml-2">{fmtPct(s.prob_winner)}</span>
      </div>
    );
  };

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <GitBranch className="text-wc-600" /> Bracket proyectado
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Top de cada fase según las 100.000 simulaciones Monte Carlo. La columna derecha es el campeón predicho.
        </p>
      </header>

      <div className="grid lg:grid-cols-6 gap-4 items-start">
        <Col title={`Octavos (Top 16)`} count={16}>
          {top16.map(rowFor)}
        </Col>
        <Col title={`Cuartos (Top 8)`} count={8}>
          {top8.map(rowFor)}
        </Col>
        <Col title={`Semifinal (Top 4)`} count={4}>
          {top4.map(rowFor)}
        </Col>
        <Col title={`Final (Top 2)`} count={2}>
          {top2.map(rowFor)}
        </Col>
        <Col title={`Campeón`} count={1}>
          {(() => {
            const t = teamByCode.get(champion.code);
            return (
              <div className="card p-4 border-l-4 border-l-wcgold-500 bg-gradient-to-br from-wcgold-50 to-white text-center">
                <Trophy className="mx-auto text-wcgold-600 mb-2" size={28} />
                <p className="text-4xl mb-1">{t?.flag_emoji}</p>
                <p className="font-bold text-slate-900">{t?.name}</p>
                <p className="text-2xl font-bold text-wcgold-700 mt-2">{fmtPct(champion.prob_winner)}</p>
                <p className="text-xs text-slate-500 mt-1">P(campeón)</p>
              </div>
            );
          })()}
        </Col>
        <Col title={`Subcampeón probable`} count={1}>
          {(() => {
            const second = top2[1];
            const t = teamByCode.get(second.code);
            return (
              <div className="card p-4 border-l-4 border-l-slate-400 bg-white text-center">
                <p className="text-4xl mb-1">{t?.flag_emoji}</p>
                <p className="font-bold text-slate-900">{t?.name}</p>
                <p className="text-2xl font-bold text-slate-700 mt-2">{fmtPct(second.prob_finalist)}</p>
                <p className="text-xs text-slate-500 mt-1">P(final)</p>
              </div>
            );
          })()}
        </Col>
      </div>

      <section className="card p-6">
        <h2 className="text-sm font-semibold text-slate-900 mb-3">Probabilidad por fase — Top 16</h2>
        <table className="w-full text-sm">
          <thead className="text-xs uppercase text-slate-500 border-b border-slate-200">
            <tr>
              <th className="text-left py-2">#</th>
              <th className="text-left py-2">Equipo</th>
              <th className="text-right py-2">Octavos</th>
              <th className="text-right py-2">Cuartos</th>
              <th className="text-right py-2">Semis</th>
              <th className="text-right py-2">Final</th>
              <th className="text-right py-2 text-wc-700">Campeón</th>
            </tr>
          </thead>
          <tbody>
            {top16.map((s, i) => {
              const t = teamByCode.get(s.code);
              return (
                <tr key={s.code} className="border-b border-slate-100 hover:bg-wc-50/50">
                  <td className="py-2 text-slate-400">{i+1}</td>
                  <td className="py-2"><TeamBadge team={t} size="md" /></td>
                  <td className="py-2 text-right">{fmtPct(s.prob_round_of_16)}</td>
                  <td className="py-2 text-right">{fmtPct(s.prob_quarterfinal)}</td>
                  <td className="py-2 text-right">{fmtPct(s.prob_semifinal)}</td>
                  <td className="py-2 text-right">{fmtPct(s.prob_finalist)}</td>
                  <td className="py-2 text-right font-semibold text-wc-700">{fmtPct(s.prob_winner)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function Col({ title, count, children }: any) {
  return (
    <div>
      <h2 className="text-xs uppercase text-slate-500 font-semibold mb-2 text-center">{title}</h2>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}
