# GameTracker: быстрый старт

## 1. Supabase
1. Создай проект на supabase.com.
2. SQL Editor -> вставь `schema.sql` -> Run.
3. Settings -> API: скопируй `Project URL`, `anon` ключ и `service_role` ключ.

## 2. Агент (Windows)
```
cd agent
pip install psutil requests pywin32
set SUPABASE_URL=https://xxxx.supabase.co
set SUPABASE_SERVICE_KEY=<service_role>
python agent.py
```
`service_role` держи только на своём ПК и никогда не клади в фронтенд или в git.
Для автозапуска: Win+R -> `shell:startup` -> ярлык на `pythonw agent.py`.
Новые игры добавляй в таблицу `games` (имя процесса смотри в Диспетчере задач).

## 3. Дашборд
```
npx create-next-app@latest web --ts --tailwind --app
```
Скопируй `web/app/page.tsx` и `web/lib/data.ts` в созданный проект, затем:
```
npm i @supabase/supabase-js
```
`.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```
`npm run dev`, затем открой http://localhost:3000
