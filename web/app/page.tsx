import { supabase, fmt } from "../data";

export default async function Home() {
  const { data: session } = await supabase
    .from("sessions")
    .select("*, games(name)")
    .order("started_at", { ascending: false })
    .limit(1)
    .single();

  return (
    <main>
      <h1>Game Time Tracker</h1>
      <div className="card">
        <h2>Текущий статус</h2>
        {session ? (
          <div>
            <p className="status-active">
              🎮 {session.games?.name || "В игре"}
            </p>
            <p className="duration">
              Длительность: <span>{fmt(session.duration_seconds)}</span>
            </p>
          </div>
        ) : (
          <p className="no-session">Нет активных игровых сессий</p>
        )}
      </div>
    </main>
  );
}