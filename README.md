# 🎮 CNTRL.GAMES

**Интеллектуальная система мониторинга цифровой активности для осознанных родителей.**

CNTRL.GAMES помогает родителям понимать, как ребёнок использует компьютер: во что играет, сколько времени, когда. Без слежки, без конфликтов, без жёстких запретов — только прозрачная статистика для здорового цифрового баланса.

🌐 **Live-демо:** [cntrlgames.vercel.app](https://cntrlgames.vercel.app)  
🤖 **Telegram-бот:** [@cntrlgame_bot](https://t.me/cntrlgame_bot)  
📥 **Скачать для Windows:** [CNTRL.GAMES-Setup.exe](https://cntrlgames.vercel.app/CNTRL.GAMES-Setup.exe)

---

## 💡 Проблема

По данным ВОЗ, **с 2019 года игровая зависимость официально признана заболеванием**. От 1 до 5% геймеров страдают от клинической формы.

Родители часто:
- Не знают, сколько времени ребёнок проводит в играх.
- Не понимают, во что именно он играет.
- Узнают о проблеме слишком поздно.
- Реагируют запретами → конфликты → потеря доверия.

## ✅ Решение

CNTRL.GAMES — это **лёгкий фоновый агент** на компьютере ребёнка + **Telegram-бот** для родителя + **веб-дашборд**. Автоматически собирает статистику, чтобы семья могла спокойно обсудить цифровой баланс.

---

## 🏗️ Архитектура
 
┌─────────────────┐      ┌──────────────┐      ┌─────────────────┐
│  Desktop Agent  │─────▶│   Supabase   │◀─────│  Telegram Bot   │
│   (Python +     │      │ (PostgreSQL) │      │   (aiogram 3)   │
│     PyQt6)      │      │              │      │                 │
└─────────────────┘      └──────┬───────┘      └─────────────────┘
│
┌──────▼───────┐
│  Web Dash    │
│  (Next.js)   │
└──────────────┘

**Компоненты:**
- **`agent/`** — Python-агент на компьютере ребёнка (GUI + трекер сессий).
- **`bot/`** — Telegram-бот для родителя (aiogram 3.x).
- **`web/`** — Next.js веб-приложение (лендинг + дашборд).
- **Supabase** — единая база данных (PostgreSQL + RLS).

---

## 🚀 Быстрый старт

### 1. Supabase

1. Создай проект на [supabase.com](https://supabase.com).
2. **SQL Editor** → вставь содержимое [`schema.sql`](./schema.sql) → **Run**.
3. **Settings → API** — скопируй:
   - `Project URL` → `SUPABASE_URL`
   - `anon` `public` ключ → `SUPABASE_KEY` (для сайта и GUI)
   - `service_role` ключ → `SUPABASE_SERVICE_KEY` (для агента и бота — **никогда не в браузер**)

### 2. Агент (Windows)

```bash
cd agent
pip install -r requirements.txt
 
Создай agent/.env:
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=<anon>
SUPABASE_SERVICE_KEY=<service_role>
BOT_TOKEN=<твой_токен_бота>
 
Запуск:
python gui.py
 
Сборка .exe:
pyinstaller --onefile --windowed --name "CNTRL.GAMES" gui.py
 
3. Telegram-бот
cd bot
pip install -r requirements.txt
python main.py
 
4. Веб-сайт
cd web
npm install
npm run dev
 
Создай web/.env.local:
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon>
 
Открой http://localhost:3000. 
 
🎯 Возможности
 
Уже работает
• ✅ Автоматический трекинг игровых сессий (Dota 2, CS2, Minecraft, Roblox и 20+ игр).
• ✅ Live-статус «сейчас играет» в Telegram.
• ✅ История сессий за любой период.
• ✅ Привязка устройства через 6-значный PIN-код.
• ✅ Поддержка нескольких устройств на одного родителя.
• ✅ Московское время в отчётах.
• ✅ Веб-лендинг с описанием продукта.
• ✅ Скачивание Windows-приложения с сайта. 
В разработке
• 🔄 Веб-дашборд с графиками и диаграммами.
• 🔄 Еженедельные отчёты в Telegram.
• 🔄 Настраиваемые лимиты («не больше 2 ч/день»).
• 🔄 Уведомления при превышении лимита.
• 🔄 Карточки игр (что развивает, какие минусы).
• 🔄 Мультиплатформенность (macOS, Linux). 
Планы
• 📋 Подписка Pro (платные тарифы).
• 📋 Мобильное приложение для родителя.
• 📋 AI-анализ паттернов поведения.
• 📋 Интеграция с детскими психологами. 
 
🛠️ Технологии
Слой Технология
Desktop Agent Python 3.11, PyQt6, psutil, pywin32
Telegram Bot Python 3.11, aiogram 3.x
Backend/DB Supabase (PostgreSQL + Row Level Security)
Web Next.js 16, React 19, TypeScript, Tailwind CSS 4
Deploy Vercel (web), PyInstaller (agent)
Version Control Git, GitHub

 
 
📁 Структура проекта
CNTRL.GAMES/
├── agent/                  # Desktop-агент
│   ├── gui.py              # PyQt6 GUI
│   ├── device_manager.py   # Управление устройством
│   ├── session_tracker.py  # Трекер игровых сессий
│   ├── process_monitor.py  # Монитор процессов
│   └── requirements.txt
├── bot/                    # Telegram-бот
│   ├── main.py
│   └── requirements.txt
├── web/                    # Веб-приложение
│   ├── app/
│   │   ├── page.tsx        # Лендинг
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── data.ts             # Supabase-клиент
│   └── package.json
├── schema.sql              # Схема базы данных
└── README.md
 
 
🗄️ Схема базы данных
• games — каталог игр (name, exe_name).
• game_sessions — игровые сессии (device_id, game_id, started_at, duration_seconds).
• now_playing — текущий статус (device_id, game_name, session_start).
• devices — устройства (device_uid, name, parent_telegram_id).
• pairing_codes — коды сопряжения (code, parent_telegram_id, expires_at, used). 
Полная схема — в schema.sql. 
 
🔐 Безопасность
• RLS-политики в Supabase защищают данные на уровне строк.
• service_role ключ используется только на сервере (агент, бот) — никогда в браузере.
• anon ключ — публичный, ограничен RLS.
• Коды сопряжения действуют 10 минут и одноразовые.
• Данные о несовершеннолетних обрабатываются в соответствии с принципами GDPR и 152-ФЗ. 
 
🎓 О проекте
 
Автор: [андрей], 14 лет
Цель: сделать цифровую среду в семье здоровой и осознанной.
Мотивация: сам играю в Dota 2 и CS — понимаю обе стороны.
 
Проект создан с нуля за несколько дней как часть обучения веб-разработке и продуктовому подходу. Open to feedback, менторству и коллаборациям. 
 
🤝 Контрибьютинг
 
Проект в активной разработке. Если хочешь помочь:
1. Fork репозиторий.
2. Создай ветку (git checkout -b feature/amazing-feature).
3. Закоммить изменения (git commit -m 'Add amazing feature').
4. Push (git push origin feature/amazing-feature).
5. Открой Pull Request. 
 
📞 Контакты
• Telegram: @origamid_1
• Email: shutenko2aa@gmail.com
• GitHub Issues: Issues 
 
📄 Лицензия
 
MIT License — см. LICENSE для деталей. 
 
🙏 Благодарности
• Учителю — за поддержку и предложение выступить на конференции.
• Родителям — за терпение и веру в проект.
• Брату — за первый тест (даже если не заработало 😄).
• Сообществам — за open-source инструменты. 
 
<div align="center">

 
⭐ Поставь звезду, если проект тебе полезен!
 
Сделано с ❤️ в 2025 году.
 
</div>
```

