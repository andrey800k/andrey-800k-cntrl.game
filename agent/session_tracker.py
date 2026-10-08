"""
CNTRL.GAMES — трекер игровых сессий.

Следит за запущенными играми, пишет сессии в Supabase
с привязкой к device_id (который даёт DeviceManager).
"""
import time
import logging
from datetime import datetime, timezone

from device_manager import DeviceManager
from process_monitor import get_running_games, register_games

log = logging.getLogger("session_tracker")


class SessionTracker:
    def __init__(self):
        self.dm = DeviceManager()
        self.supabase = self.dm.supabase
        self.device_id = None

        self.games_db = {}          # exe_name (lower) -> {"id": int, "name": str}
        self.active_sessions = {}   # exe -> {started_at, title, game_id, db_id}

    def prepare(self) -> bool:
        """
        Регистрирует устройство и синхронизирует каталог игр.
        Вызывается один раз при старте.
        """
        if not self.supabase:
            log.error("Нет клиента Supabase — трекер не может работать")
            return False

        self.device_id = self.dm.ensure_device()
        if not self.device_id:
            log.error("Не удалось зарегистрировать устройство в devices")
            return False

        self.sync_games_from_db()
        return True

    def sync_games_from_db(self):
        """Подтягивает каталог игр из games и регистрирует их в process_monitor."""
        try:
            res = self.supabase.table("games").select("id,name,exe_name").execute()
            if res.data:
                for item in res.data:
                    exe = (item.get("exe_name") or "").lower()
                    if not exe:
                        continue
                    self.games_db[exe] = {"id": item["id"], "name": item["name"]}
                    register_games({exe: (item["name"], "game")})
                log.info("Синхронизировано %d игр из Supabase", len(res.data))
        except Exception as e:
            log.warning("Ошибка синхронизации каталога игр: %s", e)

    def poll(self):
        """Один проход опроса процессов."""
        running = get_running_games(include_launchers=False, dedupe=True)
        running_exes = {g["exe"]: g for g in running}

        # 1. Закрытие сессий
        stopped = set(self.active_sessions.keys()) - set(running_exes.keys())
        for exe in stopped:
            self._end_session(exe)

        # 2. Старт новых
        for exe, info in running_exes.items():
            if exe not in self.active_sessions:
                self._start_session(exe, info["title"])

    # ------------------------------------------------------------------ games
    def _get_or_create_game_id(self, exe: str, title: str):
        exe_lower = exe.lower()
        if exe_lower in self.games_db:
            return self.games_db[exe_lower]["id"]

        try:
            res = (
                self.supabase.table("games")
                .insert({"name": title, "exe_name": exe_lower})
                .execute()
            )
            if res.data:
                new_id = res.data[0]["id"]
                self.games_db[exe_lower] = {"id": new_id, "name": title}
                register_games({exe_lower: (title, "game")})
                log.info("Новая игра добавлена в games: %s", title)
                return new_id
        except Exception as e:
            log.error("Ошибка создания игры %s: %s", title, e)

        return None

    # ------------------------------------------------------------------ session
    def _start_session(self, exe: str, title: str):
        now = time.time()
        start_iso = datetime.now(timezone.utc).isoformat()

        game_id = self._get_or_create_game_id(exe, title)
        log.info("Запущена игра: %s (%s) [game_id=%s]", title, exe, game_id)

        db_id = None
        if game_id and self.device_id:
            try:
                res = (
                    self.supabase.table("game_sessions")
                    .insert({
                        "device_id": self.device_id,
                        "game_id": game_id,
                        "started_at": start_iso,
                        "duration_seconds": 1,   # фикс из-за check constraint > 0
                    })
                    .execute()
                )
                if res.data:
                    db_id = res.data[0].get("id")
                    log.info("Создана сессия #%s", db_id)

                # Обновляем now_playing
                self.supabase.table("now_playing").update({
                    "device_id": self.device_id,
                    "game_name": title,
                    "session_start": start_iso,
                    "updated_at": start_iso,
                }).eq("id", 1).execute()

            except Exception as e:
                log.error("Ошибка записи старта сессии: %s", e)

        self.active_sessions[exe] = {
            "started_at": now,
            "title": title,
            "game_id": game_id,
            "db_id": db_id,
        }

    def _end_session(self, exe: str):
        session = self.active_sessions.pop(exe, None)
        if not session:
            return

        duration = max(1, int(time.time() - session["started_at"]))
        log.info("Игра закрыта: %s (%d сек)", session["title"], duration)

        if session["db_id"] and self.device_id:
            try:
                self.supabase.table("game_sessions").update({
                    "duration_seconds": duration,
                }).eq("id", session["db_id"]).execute()

                self.supabase.table("now_playing").update({
                    "device_id": self.device_id,
                    "game_name": None,
                    "session_start": None,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", 1).execute()

                log.info("Сессия #%s завершена (%d сек)", session["db_id"], duration)
            except Exception as e:
                log.error("Ошибка закрытия сессии: %s", e)


def run_tracker_loop(tracker: SessionTracker, poll_interval: int = 3):
    """Блокирующий цикл трекера. Запускается в отдельном QThread из GUI."""
    log.info("Трекер запущен (poll_interval=%d сек)", poll_interval)
    try:
        while True:
            try:
                tracker.poll()
            except Exception as e:
                log.exception("Ошибка в цикле трекера: %s", e)
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        log.info("Трекер остановлен")


if __name__ == "__main__":
    # Standalone-режим (без GUI): python session_tracker.py
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    tracker = SessionTracker()
    if tracker.prepare():
        run_tracker_loop(tracker)
    else:
        log.error("Трекер не смог стартовать")