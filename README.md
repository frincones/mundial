# 🏆 Mundial 2026 Predictor

> Predicciones ML para los 104 partidos del Mundial FIFA USA/CAN/MEX 2026.
> Modelo ensemble (Elo + Form + WC pedigree) sobre 49K partidos históricos + 100K simulaciones Monte Carlo.

**Demo en vivo:** https://mundial-predictor.vercel.app (TBD)

## 🎯 Predicción actual del campeón

**🇪🇸 España — 20.73%** seguido de Argentina, Francia, Inglaterra, Países Bajos.

## Arquitectura

```
mundial/
├── data/
│   ├── raw/           # martj42 49K partidos + Wikipedia squads + openfootball fixture
│   └── output/        # JSON files generados (teams, matches, predictions, simulations)
├── ml/
│   ├── seed_data.py           # 48 equipos + 12 grupos + 104 partidos fixture
│   ├── compute_real_elo.py    # Replay 49K partidos para Elo real
│   ├── compute_team_form.py   # Features de form (últimos 10, WC pedigree, etc)
│   ├── predictor.py           # Predictor baseline (Elo + Poisson)
│   └── ensemble_predictor.py  # ⭐ Ensemble de 3 modelos + 100K Monte Carlo
├── infra/
│   └── supabase/migrations/   # 0001_wc_schema.sql (tablas wc_*)
├── scripts/
│   ├── apply_migration.py     # Aplicar schema a Supabase
│   ├── load_to_supabase.py    # Cargar data desde JSON
│   └── fetch_real_data.py     # Descargar datasets externos
└── web/                       # Next.js 14 dashboard
    ├── app/                   # Pages: /, /matches, /bracket, /teams, /methodology, /stats
    ├── components/            # TeamBadge, MatchCard
    └── lib/                   # Supabase client + data fetchers
```

## Setup

```bash
# 1. Generar datos
python ml/seed_data.py            # 48 teams + 104 matches
python scripts/fetch_real_data.py # Descargar dataset martj42 (49K partidos)
python ml/compute_real_elo.py     # Elo real por team
python ml/compute_team_form.py    # Form features
python ml/ensemble_predictor.py   # ⭐ 100K simulaciones

# 2. Cargar a Supabase
python scripts/apply_migration.py
python scripts/load_to_supabase.py

# 3. Frontend
cd web
npm install
npm run dev    # http://localhost:3000
```

## Modelo ML

**Ensemble de 3 sub-modelos (peso 30%/35%/35%):**

1. **Pure Elo** — diferencia Elo + home advantage (100 pts) → Poisson para goles
2. **Elo + Form** — añade bonus por goal diff últimos 10 partidos
3. **Full** — añade pedigree WC histórico + actividad año

**Monte Carlo:** 100.000 simulaciones completas del torneo (fase grupos + eliminatoria) con Elo dinámico (K=60 grupos, 75 knockouts).

## Stack

- **Supabase** Postgres (7 tablas con prefijo `wc_`, sin auth — uso interno)
- **Next.js 14** + Tailwind + Recharts
- **Python** + numpy para ML
- **Vercel** deploy

## Datos al 21 mayo 2026

- 48 equipos confirmados (sorteo 5 dic 2025)
- 104 partidos del fixture
- 49.257 partidos internacionales históricos (1872-2026)
- Elo dinámico actualizado tras cada partido en simulación
