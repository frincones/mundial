import { BookOpen, Quote, Database, Cpu, BarChart3, Activity } from "lucide-react";

export default function MethodologyPage() {
  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <BookOpen className="text-wc-600" /> Metodología
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Cómo se construye la predicción del campeón del Mundial 2026.
        </p>
      </header>

      <section className="card p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Database size={18} className="text-wc-600" /> Fuentes de datos
        </h2>
        <ul className="text-sm space-y-2 text-slate-700">
          <li>• <strong>49.257 partidos internacionales</strong> 1872-2026 (dataset martj42, GitHub)</li>
          <li>• <strong>Fixture oficial 2026</strong>: 104 partidos (openfootball/worldcup.json)</li>
          <li>• <strong>Sorteo oficial</strong> del 5 dic 2025 (Kennedy Center, Washington DC)</li>
          <li>• <strong>Elo ratings</strong>: computados desde cero replayando los 49K partidos con K-factor variable por importancia (WC=60, qualifier=40, friendly=20)</li>
          <li>• <strong>Form features</strong>: goal diff últimos 10 partidos por selección, winrate histórico en Mundiales, actividad últimos 365 días</li>
          <li>• <strong>Wikipedia squads</strong> y FC26 player ratings (preparados pero requieren credenciales Kaggle)</li>
        </ul>
      </section>

      <section className="card p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Cpu size={18} className="text-wc-600" /> Modelo ML — Ensemble de 3
        </h2>
        <p className="text-sm text-slate-600 mb-4">
          Cada predicción se calcula como promedio ponderado de tres modelos para reducir sesgo:
        </p>
        <div className="space-y-3">
          <ModelCard
            title="Modelo 1 — Pure Elo (30%)"
            desc="Diferencia de Elo entre los dos equipos + home advantage (100 pts). Función logística sobre delta para probabilidad de victoria; Poisson independiente para goles esperados."
          />
          <ModelCard
            title="Modelo 2 — Elo + Form (35%)"
            desc="Modelo 1 + ajuste por forma reciente. Cada gol de diferencia en los últimos 10 partidos suma o resta 3 puntos de Elo efectivo. Captura momentum corto plazo que Elo puro pierde."
          />
          <ModelCard
            title="Modelo 3 — Full (35%)"
            desc="Modelo 2 + pedigree Mundial (winrate histórico en Mundiales × 60 pts Elo) + actividad año (gd_last_365d × 0.5). Premia a selecciones con historia ganadora en torneos."
          />
        </div>
        <p className="text-xs text-slate-500 italic mt-4">
          La ponderación 30/35/35 es heurística. Validado conceptualmente contra la literatura
          (Groll 2018, FiveThirtyEight SPI 2022). Próximo paso: calibración cross-validation contra
          WC 2018 + WC 2022 como holdout.
        </p>
      </section>

      <section className="card p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Activity size={18} className="text-wc-600" /> Monte Carlo (100K simulaciones)
        </h2>
        <p className="text-sm text-slate-600">
          Para cada partido del torneo simulamos 100.000 veces:
        </p>
        <ol className="text-sm space-y-1 text-slate-700 mt-3 list-decimal list-inside">
          <li><strong>Fase de grupos:</strong> 72 partidos simulados con Poisson sample (los goles son variables aleatorias).</li>
          <li><strong>Standings:</strong> se ordenan los 4 equipos del grupo por puntos → diferencia de goles → goles a favor.</li>
          <li><strong>Clasificación:</strong> 1ros + 2dos de cada grupo (24) + los 8 mejores 3ros = 32 a eliminatorias.</li>
          <li><strong>Eliminatoria:</strong> R32 → R16 → QF → SF → Final. En cada partido se simula scoreline y, si hay empate, se decide por probabilidad Elo proxy (penales).</li>
          <li><strong>Elo dinámico:</strong> dentro de cada simulación, el Elo se actualiza tras cada partido (K-factor 60 grupos, 75 knockouts).</li>
        </ol>
        <p className="text-xs text-slate-500 italic mt-4">
          Tras 100K sims, las frecuencias relativas convergen a probabilidades estables. Por ejemplo,
          si España campeona en 20.730 de 100.000 simulaciones → P(campeón) = 20.73%.
        </p>
      </section>

      <section className="card p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <BarChart3 size={18} className="text-wc-600" /> Limitaciones honestas
        </h2>
        <ul className="text-sm space-y-2 text-slate-700">
          <li>⚠️ <strong>Sin player-level data productivamente:</strong> el modelo no considera lesiones específicas de jugadores estrella (Yamal, Rodrygo, etc.). Próximo paso: integrar EAFC26 ratings.</li>
          <li>⚠️ <strong>Sin xG real:</strong> usamos proxy basado en Elo. xG verdadero requiere StatsBomb open data (limitado).</li>
          <li>⚠️ <strong>Sin venue distance/altitude:</strong> jugar en CDMX (2.250m) vs Vancouver afecta rendimiento — no modelado aún.</li>
          <li>⚠️ <strong>Modelo no calibrado contra bookmakers:</strong> próximo paso: comparar contra cuotas de casas de apuestas para Brier score.</li>
          <li>✅ <strong>Lo que sí cubre bien:</strong> diferencias estructurales de calidad (Elo histórico), forma reciente, pedigree en Mundiales, distribución estadística de goles (Poisson).</li>
        </ul>
      </section>

      <section className="card p-6 bg-slate-50/50">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <Quote size={18} className="text-wc-600" /> Referencias académicas
        </h2>
        <ul className="text-xs space-y-1.5 text-slate-600 font-mono">
          <li>• Groll et al. (2018) — Hybrid Random Forest for WC 2018 (arXiv 1806.03208)</li>
          <li>• FiveThirtyEight SPI methodology — 2022 World Cup predictions</li>
          <li>• penaltyblog (Eastwood 2025) — Better metrics for football forecasts</li>
          <li>• "From Players to Champions" (arXiv 2505.01902, mayo 2025) — ML para WC</li>
          <li>• Constantinou & Fenton — Ranked Probability Score</li>
          <li>• World Football Elo Ratings — eloratings.net method</li>
        </ul>
      </section>
    </div>
  );
}

function ModelCard({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="border border-slate-200 rounded-md p-3 bg-white">
      <p className="font-semibold text-slate-900 text-sm mb-1">{title}</p>
      <p className="text-xs text-slate-600">{desc}</p>
    </div>
  );
}
