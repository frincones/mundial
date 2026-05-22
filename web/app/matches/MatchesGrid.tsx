"use client";
import { useMemo, useState } from "react";
import { MatchCard } from "@/components/MatchCard";
import { stageLabel } from "@/lib/format";

export function MatchesGrid({ matches }: { matches: any[] }) {
  const [stage, setStage] = useState<string>("all");
  const [group, setGroup] = useState<string>("all");

  const groups = useMemo(
    () => Array.from(new Set(matches.map((m) => m.group_letter).filter(Boolean))).sort(),
    [matches]
  );
  const stages = useMemo(
    () => Array.from(new Set(matches.map((m) => m.stage))),
    [matches]
  );

  const filtered = matches.filter((m) => {
    if (stage !== "all" && m.stage !== stage) return false;
    if (group !== "all" && m.group_letter !== group) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-slate-900 mb-1">Los 104 partidos del Mundial</h1>
        <p className="text-sm text-slate-500">
          {filtered.length} de {matches.length} partidos · cada uno con predicción ML (W/D/L + scoreline esperado)
        </p>
      </header>

      <div className="flex flex-wrap gap-3 items-center">
        <select value={stage} onChange={(e) => setStage(e.target.value)} className="px-3 py-2 border border-slate-300 rounded-md text-sm bg-white">
          <option value="all">Toda la fase</option>
          {stages.map((s) => (
            <option key={s} value={s}>{stageLabel(s)}</option>
          ))}
        </select>
        <select value={group} onChange={(e) => setGroup(e.target.value)} className="px-3 py-2 border border-slate-300 rounded-md text-sm bg-white">
          <option value="all">Todos los grupos</option>
          {groups.map((g) => (
            <option key={g} value={g}>Grupo {g}</option>
          ))}
        </select>
        <span className="text-xs text-slate-400 ml-auto">
          {filtered.filter((m) => m.prob_home_win != null).length} con predicción · {filtered.filter((m) => m.prob_home_win == null).length} TBD
        </span>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((m) => (
          <MatchCard key={m.match_id} match={m} />
        ))}
      </div>
    </div>
  );
}
