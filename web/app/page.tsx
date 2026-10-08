// app/page.tsx

const Icon = ({
  name,
  className = "h-5 w-5",
}: {
  name:
    | "download"
    | "telegram"
    | "clock"
    | "eye"
    | "heart"
    | "chart"
    | "arrow"
    | "check"
    | "menu";
  className?: string;
}) => {
  const common = {
    className,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  switch (name) {
    case "download":
      return (
        <svg {...common}>
          <path d="M12 3v12" />
          <path d="m7 10 5 5 5-5" />
          <path d="M5 21h14" />
        </svg>
      );

    case "telegram":
      return (
        <svg {...common} viewBox="0 0 24 24">
          <path d="m21.5 3.5-3.3 16.1c-.25 1.14-.91 1.42-1.85.89l-5.1-3.76-2.46 2.37c-.27.27-.5.5-1.03.5l.37-5.2 9.47-8.56c.41-.37-.09-.58-.64-.21L5.25 12.87.2 11.29c-1.1-.34-1.12-1.1.23-1.63L20.2 2.1c.93-.34 1.74.21 1.3 1.4Z" />
        </svg>
      );

    case "clock":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M12 7v5l3.5 2" />
        </svg>
      );

    case "eye":
      return (
        <svg {...common}>
          <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" />
          <circle cx="12" cy="12" r="2.5" />
        </svg>
      );

    case "heart":
      return (
        <svg {...common}>
          <path d="M20.8 8.9c0 5.2-8.8 10.1-8.8 10.1S3.2 14.1 3.2 8.9A4.4 4.4 0 0 1 12 6.7a4.4 4.4 0 0 1 8.8 2.2Z" />
        </svg>
      );

    case "chart":
      return (
        <svg {...common}>
          <path d="M4 19V5" />
          <path d="M4 19h17" />
          <path d="m7 15 3-4 3 2 5-7" />
        </svg>
      );

    case "arrow":
      return (
        <svg {...common}>
          <path d="M5 12h13" />
          <path d="m13 6 6 6-6 6" />
        </svg>
      );

    case "check":
      return (
        <svg {...common}>
          <path d="m5 12 4 4L19 6" />
        </svg>
      );

    case "menu":
      return (
        <svg {...common}>
          <path d="M4 7h16" />
          <path d="M4 12h16" />
          <path d="M4 17h16" />
        </svg>
      );
  }
};

const features = [
  {
    title: "Автоматический трекинг",
    description:
      "Приложение работает в фоне и само фиксирует запуск игр, длительность сессий и активность на компьютере.",
    icon: "clock" as const,
    accent: "blue",
  },
  {
    title: "Live-статус",
    description:
      "В любой момент видно, чем занят ребёнок прямо сейчас. Без догадок и без постоянных вопросов.",
    icon: "eye" as const,
    accent: "emerald",
  },
  {
    title: "Мягкий контроль",
    description:
      "Никаких блокировок и конфликтов. Только прозрачная статистика, чтобы помочь ребёнку найти баланс.",
    icon: "heart" as const,
    accent: "blue",
  },
  {
    title: "Отчёты и статистика",
    description:
      "История сессий, время по дням, топ-игры недели, уведомления в Telegram — всё в одном месте.",
    icon: "chart" as const,
    accent: "emerald",
  },
];

const steps = [
  {
    number: "01",
    title: "Скачайте агент",
    description:
      "Установите лёгкое приложение на компьютер ребёнка. Оно работает в фоне и не мешает.",
  },
  {
    number: "02",
    title: "Привяжите через Telegram",
    description:
      "Получите 6-значный код в нашем боте и введите его в приложении.",
  },
  {
    number: "03",
    title: "Следите за статистикой",
    description:
      "Текущий статус, история, отчёты — в боте и на сайте.",
  },
];

const parentsReasons = [
  {
    title: "Никаких догадок",
    description:
      "Вы точно знаете, сколько времени ушло на развитие, а сколько — впустую.",
  },
  {
    title: "Актуальный статус",
    description:
      "Понимание того, чем занят ребёнок прямо сейчас, доступно в любой момент.",
  },
  {
    title: "Объективная картина",
    description:
      "Отчёты помогают вовремя заметить увлечения или проблемы с концентрацией.",
  },
];

const chartBars = [42, 68, 51, 82, 61, 92, 73];

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-slate-50 text-slate-900 selection:bg-blue-100 selection:text-blue-900">
      {/* Decorative background */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      >
        <div className="absolute left-1/2 top-[-20rem] h-[42rem] w-[70rem] -translate-x-1/2 rounded-full bg-blue-100/50 blur-3xl" />
        <div className="absolute right-[-15rem] top-[32rem] h-[30rem] w-[30rem] rounded-full bg-emerald-100/40 blur-3xl" />
      </div>

      {/* ================================================================ */}
      {/* NAVBAR                                                           */}
      {/* ================================================================ */}

      <header className="sticky top-0 z-50 border-b border-slate-200/70 bg-white/75 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:px-8">
          <a
            href="#top"
            className="group flex items-center gap-2.5"
            aria-label="CNTRL.GAMES — на главную"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 text-sm font-bold text-white shadow-sm transition duration-300 group-hover:scale-105">
              C
            </span>
            <span className="text-[15px] font-bold tracking-tight text-slate-900">
              CNTRL<span className="text-blue-600">.</span>GAMES
            </span>
          </a>

          <nav className="hidden items-center gap-8 md:flex">
            <a
              href="#features"
              className="text-sm font-medium text-slate-600 transition hover:text-slate-900"
            >
              Возможности
            </a>
            <a
              href="#how-it-works"
              className="text-sm font-medium text-slate-600 transition hover:text-slate-900"
            >
              Как это работает
            </a>
            <a
              href="#parents"
              className="text-sm font-medium text-slate-600 transition hover:text-slate-900"
            >
              Для родителей
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <a
              href="#download"
              className="hidden rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition duration-300 hover:-translate-y-0.5 hover:bg-slate-800 sm:inline-flex"
            >
              Скачать
            </a>

            <button
              type="button"
              aria-label="Открыть меню"
              className="rounded-xl border border-slate-200 bg-white p-2.5 text-slate-700 shadow-sm md:hidden"
            >
              <Icon name="menu" className="h-5 w-5" />
            </button>
          </div>
        </div>
      </header>

      {/* ================================================================ */}
      {/* HERO                                                             */}
      {/* ================================================================ */}

      <section id="top" className="relative">
        <div className="mx-auto max-w-7xl px-5 pb-24 pt-20 sm:px-8 sm:pt-28 lg:pb-32 lg:pt-32">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 shadow-sm">
              <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.12)]" />
              Родительский контроль нового поколения
            </div>

            <h1 className="text-5xl font-bold tracking-[-0.04em] text-slate-900 sm:text-6xl lg:text-7xl lg:leading-[1.05]">
              Цифровой баланс и развитие{" "}
              <span className="bg-gradient-to-r from-blue-600 to-blue-500 bg-clip-text text-transparent">
                вашего ребёнка
              </span>
            </h1>

            <p className="mx-auto mt-7 max-w-2xl text-lg leading-8 text-slate-600 sm:text-xl">
              CNTRL.GAMES помогает родителям понимать цифровую активность
              ребёнка: сколько времени уходит на игры, во что он играет и как
              это влияет на развитие. Без слежки, без конфликтов — только
              забота.
            </p>

            <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <a
                href="#download"
                className="group inline-flex w-full items-center justify-center gap-2.5 rounded-2xl bg-gradient-to-r from-blue-600 to-blue-500 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition duration-300 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-blue-600/25 sm:w-auto"
              >
                <Icon name="download" className="h-5 w-5" />
                Скачать для Windows
                <Icon
                  name="arrow"
                  className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5"
                />
              </a>

              <a
                href="#telegram"
                className="inline-flex w-full items-center justify-center gap-2.5 rounded-2xl border border-slate-200 bg-white px-6 py-3.5 text-sm font-semibold text-slate-800 shadow-sm transition duration-300 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md sm:w-auto"
              >
                <Icon name="telegram" className="h-5 w-5 text-blue-500" />
                Открыть в Telegram
              </a>
            </div>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs font-medium text-slate-500">
              <span>Бесплатно</span>
              <span className="h-1 w-1 rounded-full bg-slate-300" />
              <span>Windows 10/11</span>
              <span className="h-1 w-1 rounded-full bg-slate-300" />
              <span>Данные только у вас</span>
            </div>
          </div>

          {/* Hero trust strip */}
          <div className="mx-auto mt-20 max-w-4xl rounded-3xl border border-slate-200/80 bg-white/70 p-4 shadow-sm backdrop-blur">
            <div className="grid gap-4 sm:grid-cols-3">
              {[
                ["Без блокировок", "Сначала понимание, потом решение"],
                ["Прозрачно", "Без скрытого наблюдения"],
                ["Для диалога", "Помогает говорить спокойно"],
              ].map(([title, text]) => (
                <div
                  key={title}
                  className="rounded-2xl px-5 py-4 text-center sm:text-left"
                >
                  <div className="text-sm font-semibold text-slate-900">
                    {title}
                  </div>
                  <div className="mt-1 text-xs leading-5 text-slate-500">
                    {text}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* PROBLEM / FACT                                                    */}
      {/* ================================================================ */}

      <section id="why" className="border-y border-slate-200/70 bg-white">
        <div className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:py-28">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-blue-600">
              Осознанность вместо запретов
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
              Почему это важно
            </h2>
            <p className="mt-4 text-slate-600">
              Когда родители понимают реальную картину, разговор о цифровом
              времени становится спокойнее и конструктивнее.
            </p>
          </div>

          <div className="mt-12 rounded-[2rem] border border-amber-200/70 bg-gradient-to-br from-amber-50 via-white to-red-50 p-7 shadow-sm sm:p-10">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white text-2xl shadow-sm">
                🎯
              </div>
              <div>
                <p className="text-xl font-semibold leading-8 tracking-tight text-slate-900 sm:text-2xl">
                  С 2019 года ВОЗ официально признала игровую зависимость
                  (gaming disorder) заболеванием.
                </p>
                <p className="mt-3 max-w-4xl leading-7 text-slate-600">
                  По данным ВОЗ, от 1 до 5% геймеров страдают от клинической
                  формы зависимости.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-5 md:grid-cols-3">
            {[
              {
                emoji: "📊",
                title: "6 часов",
                text: "Среднее время, которое подростки проводят в играх каждую неделю.",
              },
              {
                emoji: "😴",
                title: "Нарушение сна",
                text: "Игры допоздна напрямую влияют на качество сна и успеваемость.",
              },
              {
                emoji: "🧠",
                title: "Развитие",
                text: "Не все игры одинаковы. Одни развивают стратегическое мышление, другие — просто тратят время.",
              },
            ].map((item) => (
              <article
                key={item.title}
                className="rounded-3xl border border-slate-200 bg-slate-50/70 p-7 transition duration-300 hover:-translate-y-1 hover:bg-white hover:shadow-lg hover:shadow-slate-200/60"
              >
                <div className="text-2xl">{item.emoji}</div>
                <h3 className="mt-5 text-xl font-bold">{item.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  {item.text}
                </p>
              </article>
            ))}
          </div>

          <p className="mx-auto mt-8 max-w-3xl text-center text-sm leading-6 text-slate-500">
            CNTRL.GAMES не запрещает игры. Мы помогаем семьям найти здоровый
            баланс и вовремя заметить тревожные сигналы.
          </p>
        </div>
      </section>

      {/* ================================================================ */}
      {/* FEATURES                                                          */}
      {/* ================================================================ */}

      <section id="features">
        <div className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:py-32">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-widest text-blue-600">
              Всё необходимое
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
              Контроль, который не похож на контроль
            </h2>
            <p className="mt-4 text-lg leading-7 text-slate-600">
              CNTRL.GAMES собирает факты автоматически, чтобы вам не приходилось
              спорить о том, «сколько он сегодня играл».
            </p>
          </div>

          <div className="mt-12 grid gap-5 sm:grid-cols-2">
            {features.map((feature) => (
              <article
                key={feature.title}
                className="group rounded-[2rem] border border-slate-200 bg-white p-7 shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-slate-200/60 sm:p-8"
              >
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-2xl ${
                    feature.accent === "emerald"
                      ? "bg-emerald-50 text-emerald-600"
                      : "bg-blue-50 text-blue-600"
                  }`}
                >
                  <Icon name={feature.icon} className="h-6 w-6" />
                </div>

                <h3 className="mt-7 text-xl font-bold tracking-tight">
                  {feature.title}
                </h3>

                <p className="mt-3 max-w-xl leading-7 text-slate-600">
                  {feature.description}
                </p>

                <div className="mt-6 h-px w-12 bg-slate-200 transition-all duration-300 group-hover:w-20 group-hover:bg-blue-200" />
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* HOW IT WORKS                                                      */}
      {/* ================================================================ */}

      <section
        id="how-it-works"
        className="border-y border-slate-200/70 bg-white"
      >
        <div className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-emerald-600">
              Просто начать
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
              Как это работает
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              Три простых шага — и вы видите полную картину цифровой активности.
            </p>
          </div>

          <div className="relative mt-16 grid gap-8 md:grid-cols-3 md:gap-10">
            <div
              aria-hidden="true"
              className="absolute left-[16.66%] right-[16.66%] top-8 hidden h-px bg-gradient-to-r from-blue-100 via-blue-300 to-emerald-100 md:block"
            />

            {steps.map((step) => (
              <article key={step.number} className="relative text-center">
                <div className="relative mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-blue-100 bg-white text-sm font-bold text-blue-600 shadow-md shadow-blue-100/50">
                  {step.number}
                </div>

                <h3 className="mt-7 text-xl font-bold">{step.title}</h3>

                <p className="mx-auto mt-3 max-w-sm text-sm leading-6 text-slate-600">
                  {step.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* DASHBOARD PREVIEW                                                 */}
      {/* ================================================================ */}

      <section className="relative overflow-hidden">
        <div className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:py-32">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-blue-600">
              Один взгляд — вся картина
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
              Смотрите то, что важно
            </h2>
            <p className="mt-4 text-lg leading-7 text-slate-600">
              Понятные цифры вместо бесконечных вопросов и догадок.
            </p>
          </div>

          <div className="relative mx-auto mt-14 max-w-6xl">
            <div
              aria-hidden="true"
              className="absolute -inset-6 rounded-[3rem] bg-gradient-to-r from-blue-100/50 via-white to-emerald-100/50 blur-2xl"
            />

            <div className="relative overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-2xl shadow-slate-300/40">
              {/* Dashboard header */}
              <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 sm:px-7">
                <div className="flex items-center gap-2.5">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-xs font-bold text-white">
                    C
                  </span>
                  <span className="text-sm font-bold">CNTRL.GAMES</span>
                </div>

                <div className="hidden items-center gap-3 sm:flex">
                  <span className="text-xs text-slate-400">
                    Сегодня, 8 июня
                  </span>
                  <span className="h-8 w-8 rounded-full bg-slate-100" />
                </div>
              </div>

              <div className="bg-slate-50/60 p-4 sm:p-7">
                {/* Stats */}
                <div className="grid gap-3 sm:grid-cols-3 sm:gap-4">
                  {[
                    {
                      label: "Сегодня",
                      value: "1 ч 24 мин",
                      note: "+12% к вчера",
                    },
                    {
                      label: "За неделю",
                      value: "8 ч 12 мин",
                      note: "В пределах нормы",
                    },
                    {
                      label: "Сессий",
                      value: "23",
                      note: "За последние 7 дней",
                    },
                  ].map((stat) => (
                    <div
                      key={stat.label}
                      className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                    >
                      <p className="text-xs font-medium text-slate-500">
                        {stat.label}
                      </p>
                      <p className="mt-2 text-2xl font-bold tracking-tight">
                        {stat.value}
                      </p>
                      <p className="mt-2 text-[11px] text-emerald-600">
                        {stat.note}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Chart + games */}
                <div className="mt-4 grid gap-4 lg:grid-cols-[1.6fr_1fr]">
                  <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-semibold">
                          Игровое время
                        </p>
                        <p className="mt-1 text-xs text-slate-400">
                          Последние 7 дней
                        </p>
                      </div>

                      <span className="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-600">
                        8 ч 12 мин
                      </span>
                    </div>

                    <div className="mt-8 flex h-48 items-end justify-between gap-2 border-b border-slate-100 pb-0 sm:gap-4">
                      {chartBars.map((height, index) => (
                        <div
                          key={index}
                          className="group relative flex h-full flex-1 items-end justify-center"
                        >
                          <div
                            className="w-full max-w-10 rounded-t-lg bg-gradient-to-t from-blue-600 to-blue-400 opacity-90 transition duration-300 group-hover:from-blue-500 group-hover:to-blue-300"
                            style={{ height: `${height}%` }}
                          />
                        </div>
                      ))}
                    </div>

                    <div className="mt-3 flex justify-between text-[10px] font-medium text-slate-400">
                      <span>Пн</span>
                      <span>Вт</span>
                      <span>Ср</span>
                      <span>Чт</span>
                      <span>Пт</span>
                      <span>Сб</span>
                      <span>Вс</span>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
                    <p className="text-sm font-semibold">
                      Топ-3 игры за неделю
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      По игровому времени
                    </p>

                    <div className="mt-7 space-y-5">
                      {[
                        ["Dota 2", "42%", "bg-blue-600"],
                        ["Minecraft", "31%", "bg-emerald-500"],
                        ["CS2", "18%", "bg-indigo-400"],
                      ].map(([game, percent, color], index) => (
                        <div key={game}>
                          <div className="mb-2 flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2">
                              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-slate-100 font-semibold text-slate-500">
                                {index + 1}
                              </span>
                              <span className="font-semibold text-slate-700">
                                {game}
                              </span>
                            </div>
                            <span className="font-medium text-slate-500">
                              {percent}
                            </span>
                          </div>

                          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className={`h-full rounded-full ${color}`}
                              style={{
                                width: percent,
                              }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Live status */}
                <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4 sm:flex-row sm:items-center sm:justify-between sm:px-5">
                  <div className="flex items-center gap-3">
                    <span className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-white shadow-sm">
                      <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                      <span className="absolute h-2.5 w-2.5 animate-ping rounded-full bg-emerald-400 opacity-40" />
                    </span>

                    <div>
                      <p className="text-xs text-slate-500">
                        Сейчас играет
                      </p>
                      <p className="text-sm font-semibold text-slate-900">
                        Dota 2
                      </p>
                    </div>
                  </div>

                  <span className="text-sm font-semibold text-emerald-700">
                    4 мин
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* WHY PARENTS CHOOSE US                                            */}
      {/* ================================================================ */}

      <section id="parents" className="border-y border-slate-200/70 bg-white">
        <div className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:py-32">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-emerald-600">
              Другой подход
            </p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
              Почему родители выбирают нас
            </h2>
          </div>

          <div className="mt-14 grid gap-5 md:grid-cols-3">
            {parentsReasons.map((item, index) => (
              <article
                key={item.title}
                className="rounded-[2rem] border border-slate-200 bg-slate-50/70 p-7 transition duration-300 hover:-translate-y-1 hover:bg-white hover:shadow-xl hover:shadow-slate-200/60"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white text-sm font-bold text-blue-600 shadow-sm ring-1 ring-slate-100">
                  0{index + 1}
                </div>

                <h3 className="mt-7 text-xl font-bold">{item.title}</h3>

                <p className="mt-3 leading-7 text-slate-600">
                  {item.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* FINAL CTA                                                         */}
      {/* ================================================================ */}

      <section id="download" className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-emerald-50" />

        <div className="relative mx-auto max-w-5xl px-5 py-24 text-center sm:px-8 lg:py-32">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-blue-600 shadow-lg shadow-blue-100">
            <Icon name="heart" className="h-7 w-7" />
          </div>

          <h2 className="mt-7 text-4xl font-bold tracking-[-0.03em] sm:text-5xl">
            Начните за 2 минуты
          </h2>

          <p className="mx-auto mt-5 max-w-xl text-lg leading-8 text-slate-600">
            Скачайте приложение, привяжите через Telegram — и получите полную
            картину активности.
          </p>

          <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row">
            <a
              href="#"
              className="inline-flex items-center justify-center gap-2.5 rounded-2xl bg-gradient-to-r from-blue-600 to-blue-500 px-7 py-4 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition duration-300 hover:-translate-y-0.5 hover:shadow-xl"
            >
              <Icon name="download" className="h-5 w-5" />
              Скачать для Windows
            </a>

            <a
              id="telegram"
              href="#"
              className="inline-flex items-center justify-center gap-2.5 rounded-2xl border border-slate-200 bg-white px-7 py-4 text-sm font-semibold text-slate-800 shadow-sm transition duration-300 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
            >
              <Icon name="telegram" className="h-5 w-5 text-blue-500" />
              Открыть в Telegram
            </a>
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-500">
            <span>Совместимо с Windows 10 и 11</span>
            <span>·</span>
            <span>Данные хранятся в защищённом облаке</span>
          </div>
        </div>
      </section>

      {/* ================================================================ */}
      {/* FOOTER                                                            */}
      {/* ================================================================ */}

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-7 px-5 py-10 sm:px-8 md:flex-row md:items-center md:justify-between">
          <div>
            <a
              href="#top"
              className="inline-flex items-center gap-2.5"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 text-xs font-bold text-white">
                C
              </span>
              <span className="text-sm font-bold tracking-tight">
                CNTRL<span className="text-blue-600">.</span>GAMES
              </span>
            </a>

            <p className="mt-3 text-xs text-slate-400">
              © 2026 CNTRL.GAMES. Все права защищены.
            </p>
          </div>

          <nav className="flex flex-wrap gap-x-7 gap-y-3 text-sm text-slate-500">
            <a
              href="#"
              className="transition hover:text-slate-900"
            >
              Политика конфиденциальности
            </a>
            <a
              href="mailto:support@cntrl.games"
              className="transition hover:text-slate-900"
            >
              Поддержка
            </a>
          </nav>
        </div>
      </footer>
    </main>
  );
}