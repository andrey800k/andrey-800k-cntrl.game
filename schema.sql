-- Выполни в Supabase: SQL Editor -> New query -> Run

create table if not exists public.games (
  id            bigint generated always as identity primary key,
  name          text not null unique,        -- отображаемое имя: "Dota 2"
  exe_name      text not null unique,        -- имя процесса: "dota2.exe" (нижний регистр)
  title_keyword text,                        -- запасной вариант: подстрока в заголовке окна
  created_at    timestamptz not null default now()
);

create table if not exists public.game_sessions (
  id               bigint generated always as identity primary key,
  game_id          bigint not null references public.games(id) on delete cascade,
  started_at       timestamptz not null,     -- начало отправленного отрезка
  duration_seconds integer not null check (duration_seconds > 0),
  created_at       timestamptz not null default now()
);
create index if not exists idx_sessions_started on public.game_sessions (started_at desc);
create index if not exists idx_sessions_game    on public.game_sessions (game_id);

-- Одна строка с текущим статусом (для "Сейчас в игре")
create table if not exists public.now_playing (
  id           int primary key default 1 check (id = 1),
  game_name    text,                         -- null = не в игре
  session_start timestamptz,
  updated_at   timestamptz not null default now()
);
insert into public.now_playing (id) values (1) on conflict do nothing;

-- Начальный список игр (дополняй под себя)
insert into public.games (name, exe_name, title_keyword) values
  ('Dota 2',          'dota2.exe',         'Dota 2'),
  ('Counter-Strike 2','cs2.exe',           'Counter-Strike 2'),
  ('Cyberpunk 2077',  'cyberpunk2077.exe', 'Cyberpunk 2077'),
  ('Elden Ring',      'eldenring.exe',     'ELDEN RING')
on conflict do nothing;

-- RLS: дашборд (anon-ключ) только читает; агент пишет через service_role (обходит RLS)
alter table public.games         enable row level security;
alter table public.game_sessions enable row level security;
alter table public.now_playing   enable row level security;
create policy "public read games"    on public.games         for select using (true);
create policy "public read sessions" on public.game_sessions for select using (true);
create policy "public read status"   on public.now_playing   for select using (true);
-- Для приватных данных замени using (true) на проверку auth.uid() и добавь user_id.
