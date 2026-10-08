import { createClient } from "@supabase/supabase-js";

// .env.local: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export type Session = { started_at: string; duration_seconds: number; games: { name: string } | null };

export const fmt = (sec: number) => {
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60);
  return h ? `${h} ч ${m} мин` : `${m} мин`;
};
export const dayKey = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

export async function loadDashboard() {
  const since = new Date(Date.now() - 365 * 864e5).toISOString();
  const [{ data }, { data: np }] = await Promise.all([
    supabase.from("game_sessions").select("started_at,duration_seconds,games(name)")
      .gte("started_at", since).limit(50000),
    supabase.from("now_playing").select("*").eq("id", 1).single(),
  ]);
  const sessions = (data ?? []) as unknown as Session[];

  const perDay = new Map<string, number>();   // сек за день
  const perGame = new Map<string, number>();  // сек по игре (всё время)
  const weekGame = new Map<string, number>(); // сек по игре (7 дней)
  const night = new Set<string>();            // дни с игрой после 02:00 (до 06:00)
  const now = new Date(), weekAgo = Date.now() - 7 * 864e5;
  let total = 0, week = 0;

  for (const s of sessions) {
    const d = new Date(s.started_at), k = dayKey(d), n = s.games?.name ?? "?";
    perDay.set(k, (perDay.get(k) ?? 0) + s.duration_seconds);
    perGame.set(n, (perGame.get(n) ?? 0) + s.duration_seconds);
    total += s.duration_seconds;
    if (d.getTime() >= weekAgo) {
      week += s.duration_seconds;
      weekGame.set(n, (weekGame.get(n) ?? 0) + s.duration_seconds);
    }
    if (d.getHours() >= 2 && d.getHours() < 6) night.add(k);
  }

  // стрик: дни подряд до сегодня (если сегодня ещё не играл — считаем от вчера)
  let streak = 0;
  const c = new Date(now);
  if (!perDay.has(dayKey(c))) c.setDate(c.getDate() - 1);
  while (perDay.has(dayKey(c))) { streak++; c.setDate(c.getDate() - 1); }

  const topWeek = [...weekGame.entries()].sort((a, b) => b[1] - a[1])[0];
  const live = np?.game_name && Date.now() - new Date(np.updated_at).getTime() < 150_000 ? np : null;

  return {
    today: perDay.get(dayKey(now)) ?? 0, week, total, streak, perDay,
    topWeek: topWeek ? { name: topWeek[0], sec: topWeek[1] } : null,
    games: [...perGame.entries()].sort((a, b) => b[1] - a[1]),
    live, hasNight: night.size > 0,
    marathon: [...perDay.values()].some((v) => v > 5 * 3600),
  };
}
