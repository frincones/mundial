import type { Metadata } from "next";
import Link from "next/link";
import { Trophy, Calendar, GitBranch, Users, BookOpen, BarChart3, Award } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mundial 2026 Predictor",
  description: "Predicciones ML para los 104 partidos del Mundial USA/CAN/MEX 2026",
};

const NAV = [
  { href: "/", label: "Inicio", icon: Trophy },
  { href: "/podium", label: "Podio", icon: Award },
  { href: "/matches", label: "Partidos", icon: Calendar },
  { href: "/bracket", label: "Bracket", icon: GitBranch },
  { href: "/teams", label: "Equipos", icon: Users },
  { href: "/methodology", label: "Metodología", icon: BookOpen },
  { href: "/stats", label: "Stats", icon: BarChart3 },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-2xl">🏆</span>
              <span className="font-bold text-slate-900">
                Mundial <span className="text-wc-600">2026</span>{" "}
                <span className="text-xs text-slate-400 font-normal">Predictor ML</span>
              </span>
            </Link>
            <nav className="flex items-center gap-1">
              {NAV.map((l) => {
                const I = l.icon;
                return (
                  <Link
                    key={l.href}
                    href={l.href}
                    className="px-2.5 py-1.5 rounded text-xs sm:text-sm inline-flex items-center gap-1.5 text-slate-600 hover:text-wc-700 hover:bg-wc-50 transition-colors"
                  >
                    <I size={14} /> {l.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-6 py-8 w-full">{children}</main>
        <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-400">
          Mundial 2026 Predictor · Modelo ML basado en Elo + Poisson + Monte Carlo · Datos al 21 mayo 2026
        </footer>
      </body>
    </html>
  );
}
