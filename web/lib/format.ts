export const stageLabel = (s: string) =>
  ({
    group: "Fase de grupos",
    r32: "Ronda de 32",
    r16: "Octavos",
    qf: "Cuartos",
    sf: "Semifinales",
    "3rd": "Tercer puesto",
    final: "Final",
  } as Record<string, string>)[s] || s;

export const fmtPct = (n: number) => `${(n * 100).toFixed(1)}%`;

export const fmtDate = (iso: string) => {
  try {
    const d = new Date(iso);
    return d.toLocaleString("es-CO", {
      weekday: "short", day: "2-digit", month: "short",
      hour: "2-digit", minute: "2-digit", timeZone: "America/Bogota",
    });
  } catch { return iso; }
};

export const fmtDateShort = (iso: string) => {
  try {
    const d = new Date(iso);
    return d.toLocaleString("es-CO", { day: "2-digit", month: "short", timeZone: "America/Bogota" });
  } catch { return iso; }
};

export const daysToKickoff = (): number => {
  const kickoff = new Date("2026-06-11T18:00:00Z").getTime();
  return Math.max(0, Math.ceil((kickoff - Date.now()) / (1000 * 60 * 60 * 24)));
};

export const confLabel = (c: string) =>
  ({ UEFA: "🇪🇺 UEFA", CONMEBOL: "🌎 CONMEBOL", CONCACAF: "🇲🇽 CONCACAF", AFC: "🌏 AFC", CAF: "🌍 CAF", OFC: "🇦🇺 OFC" } as Record<string,string>)[c] || c;
