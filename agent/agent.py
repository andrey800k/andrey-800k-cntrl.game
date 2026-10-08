"""
GameTracker Agent (Windows) — v3.
Раз в POLL_SEC определяет окно в фокусе -> процесс -> игра. Копит секунды, раз в минуту
отправляет в Supabase. Нет сети / ошибка БД — данные лежат в локальной SQLite-очереди.

Установка:  pip install psutil requests pywin32 python-dotenv
Запуск:     python agent.py  |  pythonw agent.py (без консоли; логи в agent.log)
.env рядом со скриптом: SUPABASE_URL, SUPABASE_SERVICE_KEY
Необязательно: SESSIONS_TABLE (по умолчанию sessions), GAMES_TABLE (games),
               STATUS_TABLE (now_playing, "" = выключить), IDLE_LIMIT_MIN (10, 0 = выкл),
               AUTO_REGISTER (1 = добавлять неизвестные игры из встроенного списка в games)
"""
import os, sys, time, json, ctypes, sqlite3, logging, datetime as dt
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import psutil, requests
import win32gui, win32process

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))

# ---------------- логи ----------------
fmt = logging.Formatter("[%(levelname)s] %(asctime)s %(message)s", "%H:%M:%S")
log = logging.getLogger("agent"); log.setLevel(logging.INFO)
fh = RotatingFileHandler(os.path.join(BASE, "agent.log"), maxBytes=1_000_000, backupCount=2, encoding="utf-8")
fh.setFormatter(fmt); log.addHandler(fh)
if sys.stdout:
    sh = logging.StreamHandler(sys.stdout); sh.setFormatter(fmt); log.addHandler(sh)

# ---------------- настройки ----------------
SB_URL, KEY = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
if not SB_URL or not KEY:
    log.error("Не заданы SUPABASE_URL / SUPABASE_SERVICE_KEY. Создай %s", os.path.join(BASE, ".env"))
    sys.exit(1)
URL  = SB_URL.rstrip("/") + "/rest/v1"
HEAD = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
T_SESS  = os.getenv("SESSIONS_TABLE", "sessions")
T_GAMES = os.getenv("GAMES_TABLE", "games")
T_STAT  = os.getenv("STATUS_TABLE", "now_playing")
IDLE_LIMIT = float(os.getenv("IDLE_LIMIT_MIN", "10")) * 60
AUTO_REG = os.getenv("AUTO_REGISTER", "1") == "1"

POLL_SEC, FLUSH_SEC, GAMES_TTL = 5, 60, 3600
GRACE_SEC = 30          # столько секунд без фокуса сессия считается "на паузе", потом закрывается
DB_PATH = os.path.join(BASE, "queue.db")

# Встроенный список: exe (нижний регистр) -> (название, подстрока заголовка или None).
# javaw.exe — это ЛЮБАЯ Java-программа, поэтому для него нужна подсказка по заголовку окна.
BUILTIN = {
    "cs2.exe": ("Counter-Strike 2", None), "dota2.exe": ("Dota 2", None),
    "gta5.exe": ("Grand Theft Auto V", None), "gtav.exe": ("Grand Theft Auto V", None),
    "rdr2.exe": ("Red Dead Redemption 2", None), "cyberpunk2077.exe": ("Cyberpunk 2077", None),
    "eldenring.exe": ("Elden Ring", None), "witcher3.exe": ("The Witcher 3", None),
    "bg3.exe": ("Baldur's Gate 3", None), "bg3_dx11.exe": ("Baldur's Gate 3", None),
    "valorant-win64-shipping.exe": ("VALORANT", None), "r5apex.exe": ("Apex Legends", None),
    "fortniteclient-win64-shipping.exe": ("Fortnite", None), "overwatch.exe": ("Overwatch 2", None),
    "league of legends.exe": ("League of Legends", None), "tslgame.exe": ("PUBG", None),
    "rocketleague.exe": ("Rocket League", None), "destiny2.exe": ("Destiny 2", None),
    "hogwartslegacy.exe": ("Hogwarts Legacy", None), "helldivers2.exe": ("Helldivers 2", None),
    "terraria.exe": ("Terraria", None), "stardew valley.exe": ("Stardew Valley", None),
    "minecraft.windows.exe": ("Minecraft", None), "javaw.exe": ("Minecraft", "minecraft"),
}

# ---------------- сеть ----------------
def api(method, path, **kw):
    r = requests.request(method, f"{URL}/{path}", headers={**HEAD, **kw.pop("headers", {})}, timeout=10, **kw)
    r.raise_for_status()
    return r

def err_text(e: Exception) -> str:
    if isinstance(e, requests.HTTPError) and e.response is not None:
        return f"{e} | {e.response.text[:200]}"
    return str(e)

# ---------------- очередь ----------------
db = sqlite3.connect(DB_PATH)
db.execute("create table if not exists q (id integer primary key, payload text)"); db.commit()
retry_at, backoff = 0.0, 10.0

def enqueue(row):
    db.execute("insert into q (payload) values (?)", (json.dumps(row),)); db.commit()

def flush_queue():
    global retry_at, backoff
    rows = db.execute("select id, payload from q order by id limit 500").fetchall()
    if not rows or time.time() < retry_at:
        return
    try:
        api("POST", T_SESS, data="[" + ",".join(p for _, p in rows) + "]")
    except requests.RequestException as e:
        retry_at = time.time() + backoff
        log.warning("Сессии не отправлены, в очереди %d. Повтор через %d с. Причина: %s",
                    len(rows), backoff, err_text(e))
        backoff = min(backoff * 2, 300)
        return
    db.execute("delete from q where id <= ?", (rows[-1][0],)); db.commit()
    backoff = 10.0
    log.info("Сессия обновлена в БД: отправлено записей %d", len(rows))

# ---------------- каталог игр ----------------
# catalog: exe -> {"id": int|None, "name": str, "hint": str|None}
catalog = {exe: {"id": None, "name": n, "hint": h} for exe, (n, h) in BUILTIN.items()}
games_loaded = 0.0

def load_games():
    global games_loaded
    cache = os.path.join(BASE, "games_cache.json")
    log.info("Ищу игры: загружаю каталог из Supabase...")
    try:
        rows = api("GET", f"{T_GAMES}?select=id,name,process_name").json()
        json.dump(rows, open(cache, "w", encoding="utf-8"))
        games_loaded = time.time()
    except requests.RequestException as e:
        log.warning("Каталог из БД недоступен (%s). Работаю со встроенным списком/кэшем.", err_text(e))
        rows = json.load(open(cache, encoding="utf-8")) if os.path.exists(cache) else []
        games_loaded = time.time() - GAMES_TTL + 60      # повтор через минуту
    for r in rows:
        exe = (r.get("process_name") or "").strip().lower()
        if exe:
            hint = catalog.get(exe, {}).get("hint")      # подсказку для javaw.exe сохраняем
            catalog[exe] = {"id": r["id"], "name": r["name"], "hint": hint}
    log.info("Игр в каталоге: %d (из БД: %d)", len(catalog), len(rows))

def ensure_id(entry) -> int | None:
    """id игры в БД; при необходимости ищет по имени или создаёт запись. None — не удалось."""
    if entry["id"]:
        return entry["id"]
    try:
        found = api("GET", f"{T_GAMES}?select=id&name=eq.{requests.utils.quote(entry['name'])}").json()
        if found:
            entry["id"] = found[0]["id"]
        elif AUTO_REG:
            exe = next(k for k, v in catalog.items() if v is entry)
            r = api("POST", T_GAMES, headers={"Prefer": "return=representation"},
                    data=json.dumps({"name": entry["name"], "process_name": exe}))
            entry["id"] = r.json()[0]["id"]
            log.info("Новая игра добавлена в БД: %s", entry["name"])
    except (requests.RequestException, KeyError, IndexError) as e:
        log.warning("Не удалось получить id для '%s': %s", entry["name"], err_text(e))
    return entry["id"]

# ---------------- статус "сейчас в игре" ----------------
status_ok = bool(T_STAT)
def set_status(name, start):
    global status_ok
    if not status_ok:
        return
    body = {"id": 1, "game_name": name, "session_start": start.isoformat() if start else None,
            "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        api("POST", f"{T_STAT}?on_conflict=id", headers={"Prefer": "resolution=merge-duplicates"},
            data=json.dumps(body))
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (400, 404):
            status_ok = False
            log.warning("Таблица статуса '%s' недоступна — отключаю live-статус (%s)", T_STAT, err_text(e))
    except requests.RequestException as e:
        log.warning("Статус не обновлён: %s", err_text(e))

# ---------------- окно и ввод ----------------
class LII(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

def idle_seconds() -> float:
    """Секунды без клавиатуры/мыши. Геймпад не учитывается — для него поставь IDLE_LIMIT_MIN=0."""
    lii = LII(); lii.cbSize = ctypes.sizeof(lii)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    return ((ctypes.windll.kernel32.GetTickCount() - lii.dwTime) & 0xFFFFFFFF) / 1000

def foreground():
    """(entry|None, exe, title) для окна в фокусе."""
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None, "", ""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        exe = psutil.Process(pid).name().lower()
    except (psutil.Error, ValueError):
        return None, "", ""
    title = win32gui.GetWindowText(hwnd)
    e = catalog.get(exe)
    if e and (not e["hint"] or e["hint"] in title.lower()):
        return e, exe, title
    return None, exe, title

# ---------------- главный цикл ----------------
def fmt_min(sec): return f"{int(sec // 60)} мин {int(sec % 60)} с"

def main():
    log.info("Агент запущен (опрос %d с, отправка %d с, AFK-лимит %s)", POLL_SEC, FLUSH_SEC,
             f"{int(IDLE_LIMIT // 60)} мин" if IDLE_LIMIT else "выкл")
    load_games()
    acc = {}                      # exe -> {"sec", "start"}  (ещё не ушло в очередь)
    cur = cur_start = lost_since = None
    sess_sec, afk, last_window = 0.0, False, None
    last_tick = last_flush = time.time()

    def close(reason):
        nonlocal cur, cur_start, lost_since, sess_sec, afk
        log.info("Сессия завершена (%s): %s, играл %s", reason, catalog[cur]["name"], fmt_min(sess_sec))
        cur = cur_start = lost_since = None; sess_sec = 0.0; afk = False
        set_status(None, None)

    while True:
        time.sleep(POLL_SEC)
        now = time.time()
        gap = now - last_tick; last_tick = now
        try:
            if now - games_loaded > GAMES_TTL:
                load_games()

            if gap > POLL_SEC * 3:                # сон / гибернация / зависание ПК
                log.warning("Пауза в работе %d с (сон ПК?) — это время не засчитываю", gap)
                if cur: close("сон/пауза ПК")
                continue

            g, exe, title = foreground()
            if (exe, title) != last_window:
                last_window = (exe, title)
                log.info("Отслеживаю окно: %s (%s)", title or "—", exe or "?")

            idle = idle_seconds()
            focused = g is not None
            if focused and IDLE_LIMIT and idle >= IDLE_LIMIT:
                if not afk: log.info("Нет ввода %d мин — пауза: %s", idle // 60, g["name"])
                afk = True
            elif focused:
                if afk: log.info("Ввод возобновился — продолжаю: %s", g["name"])
                afk = False

            if focused and not afk:
                if cur != exe:
                    if cur: close("переключился на другую игру")
                    cur, cur_start = exe, dt.datetime.now(dt.timezone.utc)
                    log.info("Обнаружена игра: %s", g["name"])
                    set_status(g["name"], cur_start)
                elif lost_since:
                    log.info("Игра снова в фокусе: %s", g["name"])
                lost_since = None
                slot = acc.setdefault(exe, {"sec": 0, "start": dt.datetime.now(dt.timezone.utc)})
                slot["sec"] += int(gap); sess_sec += gap
            elif cur and not focused:
                if lost_since is None:
                    lost_since = now
                    log.info("Игра потеряла фокус — пауза: %s", catalog[cur]["name"])
                elif now - lost_since > GRACE_SEC:
                    close("игра закрыта или свёрнута")

            if now - last_flush >= FLUSH_SEC:
                last_flush = now
                for e_, s in list(acc.items()):
                    gid = ensure_id(catalog[e_])
                    if s["sec"] > 0 and gid:
                        enqueue({"game_id": gid, "started_at": s["start"].isoformat(),
                                 "duration_seconds": s["sec"]})
                        log.info("В очередь: %s, %d с", catalog[e_]["name"], s["sec"])
                        del acc[e_]
                    elif s["sec"] > 0:
                        log.warning("Нет id игры '%s' — накопленное время сохраню до следующей попытки",
                                    catalog[e_]["name"])
                flush_queue()
                if cur and not afk:                 # heartbeat, чтобы статус не протухал
                    set_status(catalog[cur]["name"], cur_start)
        except Exception:                           # любая неожиданная ошибка не должна убить агента
            log.exception("Ошибка в цикле, продолжаю работу")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        set_status(None, None)
        log.info("Остановлено пользователем")
