"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, CartesianGrid, ScatterChart, Scatter, ZAxis } from "recharts";
import { BarChart3 } from "lucide-react";

const CONF_COLORS: Record<string, string> = {
  UEFA: "#3b82f6", CONMEBOL: "#10b981", CONCACAF: "#f59e0b",
  AFC: "#a855f7", CAF: "#ef4444", OFC: "#94a3b8",
};

export function StatsCharts({ teams, sims }: { teams: any[]; sims: any[] }) {
  const byCode = new Map(teams.map((t) => [t.code, t]));
  const top12 = [...sims].sort((a, b) => b.prob_winner - a.prob_winner).slice(0, 12);
  const data_top = top12.map((s) => ({
    name: byCode.get(s.code)?.flag_emoji + " " + (byCode.get(s.code)?.name.slice(0, 15) || s.code),
    prob_winner: +(s.prob_winner * 100).toFixed(2),
    prob_finalist: +(s.prob_finalist * 100).toFixed(2),
  }));

  // Pie por confederación de los top 16
  const top16 = [...sims].sort((a, b) => b.prob_winner - a.prob_winner).slice(0, 16);
  const byConf: Record<string, number> = {};
  for (const s of top16) {
    const c = byCode.get(s.code)?.confederation || "OFC";
    byConf[c] = (byConf[c] || 0) + s.prob_winner;
  }
  const pieData = Object.entries(byConf).map(([conf, p]) => ({ name: conf, value: +(p * 100).toFixed(1) }));

  // Scatter Elo vs P(campeón)
  const scatter = sims.map((s) => {
    const t = byCode.get(s.code);
    return {
      name: t?.name,
      elo: Math.round(t?.elo_rating || 0),
      prob: +(s.prob_winner * 100).toFixed(2),
      conf: t?.confederation || "OFC",
    };
  });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <BarChart3 className="text-wc-600" /> Estadísticas
        </h1>
        <p className="text-sm text-slate-500">Distribución de probabilidades por confederación y por equipo</p>
      </header>

      <div className="card p-6">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">Top 12 — probabilidad de campeón vs finalista</h2>
        <div style={{ width: "100%", height: 340 }}>
          <ResponsiveContainer>
            <BarChart data={data_top} margin={{ left: 10, right: 12, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" angle={-25} textAnchor="end" interval={0} tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="prob_finalist" fill="#cbd5e1" name="Finalista %" />
              <Bar dataKey="prob_winner" fill="#d92d20" name="Campeón %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">P(campeón) acumulada por confederación</h2>
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                  {pieData.map((d, i) => <Cell key={i} fill={CONF_COLORS[d.name] || "#94a3b8"} />)}
                </Pie>
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card p-6">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">Correlación: Elo rating vs probabilidad de campeón</h2>
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <ScatterChart margin={{ left: 10, right: 12, bottom: 12 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" dataKey="elo" name="Elo" tick={{ fontSize: 11 }} domain={[1450, 2300]} />
                <YAxis type="number" dataKey="prob" name="P(campeón)" unit="%" tick={{ fontSize: 11 }} />
                <ZAxis range={[60, 120]} />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} formatter={(v: any, _n: any, p: any) => [v, p?.payload?.name]} />
                <Scatter data={scatter} fill="#d92d20" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
