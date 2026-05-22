import Link from "next/link";

export function TeamBadge({
  team,
  size = "md",
  link = true,
}: {
  team: { code: string; name: string; flag_emoji?: string } | null;
  size?: "sm" | "md" | "lg";
  link?: boolean;
}) {
  if (!team) {
    return <span className="text-slate-400 italic text-sm">TBD</span>;
  }
  const sizes = {
    sm: "text-xs gap-1",
    md: "text-sm gap-1.5",
    lg: "text-base gap-2",
  };
  const flagSize = { sm: "text-base", md: "text-lg", lg: "text-2xl" };
  const content = (
    <span className={`inline-flex items-center ${sizes[size]}`}>
      <span className={flagSize[size]}>{team.flag_emoji}</span>
      <span className="font-medium text-slate-800">{team.name}</span>
    </span>
  );
  return link ? <Link href={`/teams/${team.code}`} className="hover:text-wc-700">{content}</Link> : content;
}
