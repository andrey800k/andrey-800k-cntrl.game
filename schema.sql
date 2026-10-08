-- ============================================================
-- CNTRL.GAMES — Supabase schema v2
-- Выполни в Supabase: SQL Editor -> New query -> Run
-- ============================================================

-- ---------- 1. Устройства ----------
create table if not exists public.devices (
  id                 bigint generated always as identity primary key,
  device_uid         text not null unique,        -- UUID с ПК (gui.py генерирует)
  name               text,                        -- имя компьютера (platform.node)
  os                 text,                        -- версия ОС
  parent_id          text,                        -- ID родителя (из pairing_codes)
  parent_telegram_id bigint,                      -- Telegram ID родителя (для бота)
  is_active          boolean not null default true,
  linked_at          timestamptz,
  last_seen          timestamptz
);
create index if not exists idx_devices_parent_tg on public.devices (parent_telegram_id);

-- ---------- 2. Коды сопряжения ----------
create table if not exists public.pairing_codes (
  id                 bigint generated always as identity primary key,
  code               text not null unique,         -- 6-значный PIN
  device_id          bigint references public.devices(id) on delete cascade,
  parent_id          text,                         -- ID родителя
  parent_telegram_id bigint,                       -- Telegram ID (после привязки через бота)
  used               boolean not null default false,
  used_at            timestamptz,
  expires_at         timestamptz not null
);
create index if not exists idx_pairing_code on public.pairing_codes (code);

-- ---------- 3. Каталог игр ----------
create table if not exists public.games (
  id            bigint generated always as identity primary key,
  name          text not null unique,
  exe_name      text unique,                       -- agent/session_tracker.py использует это поле
  created_at    timestamptz not null default now()
);

-- ---------- 4. Игровые сессии ----------
create table if not exists public.game_sessions (
  id               bigint generated always as identity primary key,
  device_id        bigint references public.devices(id) on delete cascade,
  game_id          bigint not null references public.games(id) on delete cascade,
  started_at       timestamptz not null,
  duration_seconds integer not null check (duration_seconds > 0),
  created_at       timestamptz not null default now()
);
create index if not exists idx_sessions_device  on public.game_sessions (device_id);
create index if not exists idx_sessions_started on public.game_sessions (started_at desc);

-- ---------- 5. Текущий статус ----------
create table if not exists public.now_playing (
  id            int primary key default 1 check (id = 1),
  device_id     bigint,                            -- для будущего multi-device
  game_name     text,
  session_start timestamptz,
  updated_at    timestamptz not null default now()
);
insert into public.now_playing (id) values (1) on conflict do nothing;

-- ---------- 6. Стартовый каталог игр ----------
insert into public.games (name, exe_name) values
  ('Dota 2',           'dota2.exe'),
  ('Counter-Strike 2', 'cs2.exe'),
  ('Cyberpunk 2077',   'cyberpunk2077.exe'),
  ('Elden Ring',       'eldenring.exe'),
  ('Roblox',           'robloxplayerbeta.exe'),
  ('Minecraft',        'javaw.exe')
on conflict do nothing;

-- ---------- 7. RLS ----------
alter table public.games          enable row level security;
alter table public.game_sessions  enable row level security;
alter table public.now_playing    enable row level security;
alter table public.devices        enable row level security;
alter table public.pairing_codes  enable row level security;

-- Агент пишет через service_role (обходит RLS). GUI и бот — через anon.
-- Для MVP: разрешаем всё — потом ужесточим.
create policy "allow all games"    on public.games          for all using (true) with check (true);
create policy "allow all sessions" on public.game_sessions  for all using (true) with check (true);
create policy "allow all status"   on public.now_playing    for all using (true) with check (true);
create policy "allow all devices"  on public.devices        for all using (true) with check (true);
create policy "allow all codes"    on public.pairing_codes  for all using (true) with check (true);
