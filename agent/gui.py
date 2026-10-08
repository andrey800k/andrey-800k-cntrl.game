"""
CNTRL.GAMES — GUI десктопного агента (PyQt6).

Установка:  pip install PyQt6 supabase python-dotenv
Настройка:  файл .env рядом со скриптом: SUPABASE_URL=...  SUPABASE_KEY=...
Запуск:     python gui.py          (обычный режим)
            python gui.py --demo   (имитация игры, чтобы посмотреть интерфейс)

Интеграция:
  * сигнал  window.pin_submitted(str)       -> PIN проверяет PinVerifierWorker (Supabase)
  * слот    window.set_linked(bool)         -> результат привязки
  * слот    window.show_link_error(str)     -> показать ошибку под полем PIN
  * слот    window.set_activity(name, dt)   -> текущая игра (None, None = не играет)
Вызывай слоты из потока трекера через pyqtSignal, а не напрямую (Qt не потокобезопасен).
"""
import os, sys, uuid, logging, platform
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv
from supabase import create_client
from supabase.client import ClientOptions
from postgrest.exceptions import APIError

from PyQt6.QtCore import Qt, QTimer, QRegularExpression, pyqtSignal, pyqtSlot, QSettings, QThread
from PyQt6.QtGui import (QAction, QColor, QFont, QIcon, QPainter, QPixmap,
                         QRegularExpressionValidator, QLinearGradient, QBrush)
from PyQt6.QtWidgets import (QApplication, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
                             QLabel, QLineEdit, QMenu, QPushButton, QSystemTrayIcon,
                             QVBoxLayout, QWidget)

APP_NAME, VERSION = "CNTRL.GAMES", "v1.0 MVP"

# ---------------------------------------------------------------- Supabase
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
SB_URL, SB_KEY = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
T_CODES, T_DEVICES = "pairing_codes", "devices"
BAD_PIN = "Неверный или просроченный PIN"
log = logging.getLogger("gui")

# ---------------------------------------------------------------- стили
STYLE = """
* { font-family: 'Segoe UI', 'Inter', sans-serif; color: #0F172A; }
QWidget#root { background: #F8FAFC; }
QFrame#card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }
QLabel { background: transparent; }
QLabel#title { font-size: 22px; font-weight: 800; letter-spacing: 1px; }
QLabel#badge { background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE;
               border-radius: 10px; padding: 2px 10px; font-size: 11px; font-weight: 700; }
QLabel#cardTitle { font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px; }
QLabel#hint { color: #64748B; font-size: 12px; }
QLabel#error { color: #B91C1C; font-size: 12px; }
QLabel#pill { border-radius: 12px; padding: 6px 14px; font-size: 13px; font-weight: 600; }
QLabel#pill[linked="false"] { background: #FEF2F2; color: #B91C1C; border: 1px solid #FECACA; }
QLabel#pill[linked="true"]  { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
QLineEdit#pin { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px;
                padding: 12px; font-size: 26px; font-weight: 700; letter-spacing: 12px; }
QLineEdit#pin:focus { border: 2px solid #2563EB; background: #FFFFFF; }
QLineEdit#pin:disabled { color: #94A3B8; background: #F1F5F9; }
QPushButton#primary { color: #FFFFFF; font-size: 14px; font-weight: 700; border: none;
    border-radius: 12px; padding: 12px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2563EB, stop:1 #0284C7); }
QPushButton#primary:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1D4ED8, stop:1 #0369A1); }
QPushButton#primary:disabled { background: #E2E8F0; color: #94A3B8; }
QLabel#game { font-size: 18px; font-weight: 700; }
QLabel#timer { font-size: 13px; color: #0284C7; font-weight: 600; }
"""


def make_icon() -> QIcon:
    """Иконка приложения рисуется кодом — внешние файлы не нужны."""
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    g = QLinearGradient(0, 0, 64, 64)
    g.setColorAt(0, QColor("#2563EB")); g.setColorAt(1, QColor("#0284C7"))
    p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(2, 2, 60, 60, 16, 16)
    p.setPen(QColor("white")); p.setFont(QFont("Segoe UI", 30, QFont.Weight.Black))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "C")
    p.end()
    return QIcon(pm)


def fmt_duration(sec: float) -> str:
    h, m = int(sec // 3600), int(sec % 3600 // 60)
    return f"{h} ч {m} мин" if h else f"{m} мин"


class Card(QFrame):
    """Белая карточка с мягкой тенью и заголовком."""
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("card")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24); shadow.setOffset(0, 4); shadow.setColor(QColor(15, 23, 42, 25))
        self.setGraphicsEffect(shadow)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(20, 16, 20, 18); self.body.setSpacing(10)
        lbl = QLabel(title.upper()); lbl.setObjectName("cardTitle")
        self.body.addWidget(lbl)


class LinkError(Exception):
    """Ошибка привязки. Текст (str) безопасно показывать пользователю."""


def get_device_uid() -> str:
    """Постоянный id этого ПК (создаётся один раз, хранится в QSettings)."""
    st = QSettings("CNTRL", "GamesAgent")
    if not st.contains("device_uid"):
        st.setValue("device_uid", str(uuid.uuid4()))
    return str(st.value("device_uid"))


def _make_client():
    if not SB_URL or not SB_KEY:
        raise LinkError("Не настроен .env (SUPABASE_URL / SUPABASE_KEY)")
    return create_client(SB_URL, SB_KEY, options=ClientOptions(postgrest_client_timeout=10))


def _step_error(step: str, e: APIError) -> LinkError:
    """Подробно пишет ошибку Supabase в лог и возвращает понятное сообщение для UI."""
    msg, code = getattr(e, "message", str(e)), getattr(e, "code", "")
    log.error("[%s] APIError code=%s message=%s details=%s hint=%s",
              step, code, msg, getattr(e, "details", None), getattr(e, "hint", None))
    rls = " Нет прав: проверьте RLS-политики таблицы." if code == "42501" or "row-level" in str(msg).lower() else ""
    return LinkError(f"Шаг «{step}»: {msg}.{rls}")


def link_device(code: str, device_uid: str | None = None) -> str:
    """
    Привязка ПК по PIN.
    Возвращает parent_telegram_id (строкой) или бросает LinkError (сообщение для UI).
    Сетевые ошибки (httpx.TransportError) пробрасываются — их обрабатывает вызывающий.
    Шаги:
      1) SELECT pairing_codes по коду
      2) UPSERT devices с parent_telegram_id
      3) UPDATE pairing_codes.used = true
      4) контрольный SELECT devices
    """
    code, uid = code.strip(), device_uid or get_device_uid()
    sb, now = _make_client(), datetime.now(timezone.utc).isoformat()
    log.info("Привязка: PIN=%s device_uid=%s", code, uid)

    # 1) SELECT pairing_codes
    try:
        rows = (sb.table(T_CODES).select("id,parent_telegram_id")
                .eq("code", code).eq("used", False)
                .gt("expires_at", now).limit(1).execute().data)
    except APIError as e:
        raise _step_error("поиск PIN", e)
    log.info("SELECT %s: найдено строк: %d", T_CODES, len(rows))
    if not rows:
        log.warning("PIN не найден/использован/истёк. Если PIN точно верный — проверьте SELECT-политику RLS.")
        raise LinkError(BAD_PIN)

    row = rows[0]
    parent_tg_id = row.get("parent_telegram_id")
    if not parent_tg_id:
        raise LinkError("PIN не привязан к Telegram-родителю. Создайте новый код в боте.")

    # 2) UPSERT devices
    try:
        res = sb.table(T_DEVICES).upsert({
            "device_uid": uid,
            "parent_telegram_id": parent_tg_id,
            "name": platform.node(),
            "os": platform.platform(),
            "is_active": True,
            "linked_at": now,
            "last_seen": now,
        }, on_conflict="device_uid").execute()
    except APIError as e:
        raise _step_error("запись устройства", e)
    if not res.data:
        log.error("upsert devices вернул пустой ответ — запись, вероятно, не создана (RLS?)")
        raise LinkError("Шаг «запись устройства»: Supabase не подтвердил запись. Проверьте RLS-политики devices.")
    log.info("UPSERT %s: ок, id=%s", T_DEVICES, res.data[0].get("id"))

    # 3) UPDATE pairing_codes.used = true
    try:
        upd = (sb.table(T_CODES).update({"used": True, "used_at": now})
               .eq("id", row["id"]).eq("used", False).execute().data)
    except APIError as e:
        raise _step_error("погашение PIN", e)
    if not upd:
        log.error("UPDATE %s не изменил ни одной строки (PIN уже использован или нет UPDATE-политики)", T_CODES)
        raise LinkError("Шаг «погашение PIN»: код не удалось пометить использованным (уже занят или нет прав UPDATE).")
    log.info("UPDATE %s: used=true для id=%s", T_CODES, row["id"])

    # 4) контрольный SELECT
    try:
        chk = sb.table(T_DEVICES).select("id").eq("device_uid", uid).limit(1).execute().data
    except APIError as e:
        raise _step_error("проверка записи", e)
    if not chk:
        raise LinkError("Запись устройства не читается после вставки. Проверьте SELECT-политику devices.")

    log.info("Привязка завершена, parent_telegram_id=%s", parent_tg_id)
    return str(parent_tg_id)


class PinVerifierWorker(QThread):
    """Выполняет link_device() в отдельном потоке, чтобы GUI не зависал."""
    success_signal = pyqtSignal(str)   # parent_telegram_id
    error_signal = pyqtSignal(str)     # текст ошибки для пользователя

    def __init__(self, pin: str, device_uid: str, parent=None):
        super().__init__(parent)
        self.pin, self.device_uid = pin, device_uid

    def run(self):
        try:
            self.success_signal.emit(link_device(self.pin, self.device_uid))
        except LinkError as e:
            self.error_signal.emit(str(e))
        except (httpx.TransportError, OSError) as e:      # нет интернета, DNS, таймаут
            log.error("Сетевая ошибка: %r", e)
            self.error_signal.emit("Нет подключения к интернету. Проверьте сеть и попробуйте снова.")
        except Exception as e:
            log.exception("Непредвиденная ошибка привязки")
            self.error_signal.emit(f"Не удалось выполнить привязку: {type(e).__name__}: {e}"[:160])


class LinkCheckWorker(QThread):
    """При запуске проверяет, что сохранённая «привязка» реально есть в devices."""
    result = pyqtSignal(bool)

    def __init__(self, device_uid: str, parent=None):
        super().__init__(parent)
        self.device_uid = device_uid

    def run(self):
        try:
            rows = (_make_client().table(T_DEVICES).select("id").eq("device_uid", self.device_uid)
                    .eq("is_active", True).limit(1).execute().data)
            self.result.emit(bool(rows))
        except Exception as e:      # нет сети и т.п. — состояние не трогаем
            log.warning("Проверка привязки пропущена: %r", e)


class TrackerWorker(QThread):
    """Крутит session_tracker в отдельном потоке, чтобы GUI не блокировался."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tracker = None

    def run(self):
        # Импорт внутри run(), чтобы не тянуть session_tracker на этапе загрузки GUI
        from session_tracker import SessionTracker, run_tracker_loop

        self.tracker = SessionTracker()
        if not self.tracker.prepare():
            log.error("Трекер не стартовал — Supabase недоступен или нет device_id")
            return
        run_tracker_loop(self.tracker, poll_interval=3)


class MainWindow(QWidget):
    pin_submitted = pyqtSignal(str)   # 6-значный PIN -> наружу (Supabase / бот)

    def __init__(self):
        super().__init__()
        self.settings = QSettings("CNTRL", "GamesAgent")   # запоминаем статус привязки
        self.linked = self.settings.value("linked", False, type=bool)
        self._game: str | None = None
        self._started: datetime | None = None
        self._quitting = False
        self._worker: PinVerifierWorker | None = None
        self.tracker_thread: TrackerWorker | None = None
        if not self.settings.contains("device_uid"):      # постоянный id этого ПК
            self.settings.setValue("device_uid", str(uuid.uuid4()))
        self.device_uid = str(self.settings.value("device_uid"))

        self.setObjectName("root")
        self.setWindowTitle(APP_NAME); self.setWindowIcon(make_icon())
        self.setFixedSize(420, 600)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24); root.setSpacing(16)
        root.addLayout(self._build_header())
        root.addWidget(self._build_status(), alignment=Qt.AlignmentFlag.AlignLeft)
        root.addWidget(self._build_pin_card())
        root.addWidget(self._build_activity_card())
        root.addStretch()

        self._build_tray()
        self.set_linked(self.linked)
        self.set_activity(None, None)
        self.pin_submitted.connect(self._start_verification)
        self._check: LinkCheckWorker | None = None
        if self.linked:     # флаг мог остаться от старой заглушки — сверяем с базой
            self._check = LinkCheckWorker(self.device_uid, self)
            self._check.result.connect(self._on_link_checked)
            self._check.start()

        self.clock = QTimer(self, interval=1000)   # живой таймер сессии
        self.clock.timeout.connect(self._tick); self.clock.start()

        # Запускаем трекер в фоне
        self.tracker_thread = TrackerWorker(self)
        self.tracker_thread.start()

    # ------------------------------------------------ построение UI
    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        title = QLabel(APP_NAME); title.setObjectName("title")
        badge = QLabel(VERSION); badge.setObjectName("badge")
        row.addWidget(title); row.addWidget(badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        row.addStretch()
        return row

    def _build_status(self) -> QLabel:
        self.pill = QLabel(); self.pill.setObjectName("pill")
        return self.pill

    def _build_pin_card(self) -> Card:
        card = Card("Привязка к Telegram")
        hint = QLabel("Получите PIN у бота родителя и введите его ниже.")
        hint.setObjectName("hint"); hint.setWordWrap(True)

        self.pin = QLineEdit(); self.pin.setObjectName("pin")
        self.pin.setMaxLength(6); self.pin.setPlaceholderText("······")
        self.pin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pin.setValidator(QRegularExpressionValidator(QRegularExpression(r"\d{0,6}")))
        self.pin.textChanged.connect(self._on_pin_changed)
        self.pin.returnPressed.connect(self._on_link_clicked)

        self.error = QLabel(); self.error.setObjectName("error"); self.error.hide()

        self.btn = QPushButton("Привязать ПК"); self.btn.setObjectName("primary")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(self._on_link_clicked)

        for w in (hint, self.pin, self.error, self.btn):
            card.body.addWidget(w)
        return card

    def _build_activity_card(self) -> Card:
        card = Card("Текущая активность")
        self.game_lbl = QLabel(); self.game_lbl.setObjectName("game"); self.game_lbl.setWordWrap(True)
        self.timer_lbl = QLabel(); self.timer_lbl.setObjectName("timer")
        card.body.addWidget(self.game_lbl); card.body.addWidget(self.timer_lbl)
        return card

    def _build_tray(self):
        self.tray = QSystemTrayIcon(make_icon(), self)
        menu = QMenu()
        act_open = QAction("Открыть", self, triggered=self.show_window)
        act_status = QAction("Статус", self, triggered=self.show_status)
        act_hide = QAction("Свернуть", self, triggered=self.hide)
        act_quit = QAction("Выход", self, triggered=self.quit_app)
        for a in (act_open, act_status, act_hide):
            menu.addAction(a)
        menu.addSeparator(); menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self._tray_menu = menu          # держим ссылку, иначе меню соберёт GC
        self.tray.show()

    # ------------------------------------------------ публичный API
    @pyqtSlot(bool)
    def set_linked(self, linked: bool):
        self.linked = linked
        self.settings.setValue("linked", linked)
        self.pill.setText("🟢  Активен и защищен" if linked else "🔴  Не привязан")
        self.pill.setProperty("linked", "true" if linked else "false")
        self.pill.style().unpolish(self.pill); self.pill.style().polish(self.pill)  # применить QSS
        self.pin.setEnabled(not linked)
        self.btn.setText("ПК привязан ✓" if linked else "Привязать ПК")
        self.btn.setEnabled(False if linked else len(self.pin.text()) == 6)
        if linked:
            self.pin.clear(); self.error.hide()
        self.tray.setToolTip(f"{APP_NAME} — {'активен' if linked else 'не привязан'}")

    @pyqtSlot(str)
    def show_link_error(self, msg: str):
        self.error.setText(msg); self.error.show()
        self.btn.setText("Привязать ПК")
        self.btn.setEnabled(len(self.pin.text()) == 6)
        self.pin.setEnabled(True)

    @pyqtSlot(object, object)
    def set_activity(self, game: str | None, started_at: datetime | None):
        self._game, self._started = game, started_at
        self._tick()

    # ------------------------------------------------ внутренние слоты
    def _tick(self):
        if self._game and self._started:
            sec = max((datetime.now() - self._started).total_seconds(), 0)
            self.game_lbl.setText(f"{self._game} • {fmt_duration(sec)}")
            self.timer_lbl.setText(f"● В игре  {int(sec // 3600):02d}:{int(sec % 3600 // 60):02d}:{int(sec % 60):02d}")
        else:
            self.game_lbl.setText("Сейчас не играете")
            self.timer_lbl.setText("○ Ожидание игры")

    def _on_pin_changed(self, text: str):
        self.error.hide()
        self.btn.setEnabled(len(text) == 6 and not self.linked)

    def _on_link_clicked(self):
        pin = self.pin.text()
        if len(pin) != 6 or self.linked:
            return
        self.btn.setEnabled(False); self.btn.setText("Проверяем…"); self.pin.setEnabled(False)
        self.pin_submitted.emit(pin)

    def _start_verification(self, pin: str):
        """Запускает проверку PIN в фоновом потоке."""
        if self._worker and self._worker.isRunning():
            return
        self._worker = PinVerifierWorker(pin, self.device_uid, self)
        self._worker.success_signal.connect(self._on_link_success)
        self._worker.error_signal.connect(self.show_link_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    @pyqtSlot(str)
    def _on_link_success(self, parent_telegram_id: str):
        self.settings.setValue("parent_telegram_id", parent_telegram_id)   # связка устройства с родителем
        self.set_linked(True)
        self.tray.showMessage(APP_NAME, "ПК успешно привязан. Защита активна.",
                              QSystemTrayIcon.MessageIcon.Information, 3000)

    @pyqtSlot(bool)
    def _on_link_checked(self, exists: bool):
        if not exists:
            log.warning("В devices нет записи для этого ПК — сбрасываю статус «Привязан»")
            self.set_linked(False)

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_window()

    def show_window(self):
        self.showNormal(); self.raise_(); self.activateWindow()

    def show_status(self):
        link = "привязан, защита активна" if self.linked else "не привязан к Telegram"
        play = f"{self._game} • {fmt_duration((datetime.now() - self._started).total_seconds())}" \
            if self._game and self._started else "сейчас не играете"
        self.tray.showMessage(APP_NAME, f"ПК {link}\n{play}", QSystemTrayIcon.MessageIcon.Information, 4000)

    def quit_app(self):
        self._quitting = True
        if self._worker and self._worker.isRunning():
            self._worker.wait(3000)
        if self.tracker_thread and self.tracker_thread.isRunning():
            self.tracker_thread.terminate()
            self.tracker_thread.wait(2000)
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        """Крестик не завершает агент — окно уходит в трей."""
        if self._quitting:
            event.accept(); return
        event.ignore(); self.hide()
        self.tray.showMessage(APP_NAME, "Агент продолжает работать в фоне. Выход — через меню в трее.",
                              QSystemTrayIcon.MessageIcon.Information, 3000)


# ---------------------------------------------------------------- запуск
def main():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s %(message)s",
                        datefmt="%H:%M:%S", handlers=[logging.StreamHandler(),
                        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                        "gui.log"), encoding="utf-8")])
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    app.setQuitOnLastWindowClosed(False)       # процесс живёт, пока есть трей
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("[WARN] Системный трей недоступен")

    win = MainWindow()

    if "--demo" in sys.argv:                   # имитация игровой сессии
        win.set_activity("Counter-Strike 2", datetime.now() - timedelta(minutes=42))

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()