import Link from "next/link";
import { TeamBadge } from "./TeamBadge";
import { fmtDateShort, stageLabel } from "@/lib/format";

export function MatchCard({ match }: { match: any }) {
  const has = !!match.home_team_code && !!match.away_team_code;
  const p = match.prob_home_win != null ? match : null;

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-2 text-xs text-slate-500">
        <span className="badge-neutral">
          {match.group_letter ? `Grupo ${match.group_letter}` : stageLabel(match.stage)} · #{match.match_number}
        </span>
        <span>
          {fmtDateShort(match.scheduled_at)} · {match.venue_city}
        </span>
      </div>

      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 mb-3">
        <div className="text-right">
          {has ? (
            <TeamBadge
              team={{ code: match.home_team_code, name: match.home_name, flag_emoji: match.home_flag }}
              size="md"
            />
          ) : (
            <span className="text-xs text-slate-400">{match.home_label || "TBD"}</span>
          )}
        </div>
        <div className="text-center font-bold text-slate-300">vs</div>
        <div className="text-left">
          {has ? (
            <TeamBadge
              team={{ code: match.away_team_code, name: match.away_name, flag_emoji: match.away_flag }}
              size="md"
            />
          ) : (
            <span className="text-xs text-slate-400">{match.away_label || "TBD"}</span>
          )}
        </div>
      </div>

      {p && (
        <>
          <div className="prob-bar mb-1.5">
            <div className="prob-fill-home" style={{ width: `${p.prob_home_win * 100}%` }} />
            <div className="prob-fill-draw" style={{ left: `${p.prob_home_win * 100}%`, width: `${p.prob_draw * 100}%` }} />
            <div className="prob-fill-away" style={{ width: `${p.prob_away_win * 100}%` }} />
          </div>
          <div className="grid grid-cols-3 gap-1 text-xs text-center">
            <div className="text-blue-700 font-medium">
              {(p.prob_home_win * 100).toFixed(0)}%
            </div>
            <div className="text-slate-500">{(p.prob_draw * 100).toFixed(0)}% E</div>
            <div className="text-rose-700 font-medium">
              {(p.prob_away_win * 100).toFixed(0)}%
            </div>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500 text-center">
            Resultado más probable: <span className="font-semibold text-slate-700">{p.predicted_scoreline}</span>
            {" · "}xG {p.expected_home_goals.toFixed(1)}-{p.expected_away_goals.toFixed(1)}
          </div>
        </>
      )}
    </div>
  );
}
