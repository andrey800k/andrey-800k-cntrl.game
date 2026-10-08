"""
CNTRL.GAMES — GUI десктопного агента (PyQt6).

Установка:  pip install PyQt6
Запуск:     python gui.py          (обычный режим)
            python gui.py --demo   (имитация игры, чтобы посмотреть интерфейс)

Интеграция:
  * сигнал  window.pin_submitted(str)       -> отправь PIN в Supabase / бот
  * слот    window.set_linked(bool)         -> результат привязки
  * слот    window.show_link_error(str)     -> показать ошибку под полем PIN
  * слот    window.set_activity(name, dt)   -> текущая игра (None, None = не играет)
Вызывай слоты из потока трекера через pyqtSignal, а не напрямую (Qt не потокобезопасен).
"""
import sys
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QTimer, QRegularExpression, pyqtSignal, pyqtSlot, QSettings
from PyQt6.QtGui import (QAction, QColor, QFont, QIcon, QPainter, QPixmap,
                         QRegularExpressionValidator, QLinearGradient, QBrush)
from PyQt6.QtWidgets import (QApplication, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
                             QLabel, QLineEdit, QMenu, QPushButton, QSystemTrayIcon,
                             QVBoxLayout, QWidget)

APP_NAME, VERSION = "CNTRL.GAMES", "v1.0 MVP"

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


class MainWindow(QWidget):
    pin_submitted = pyqtSignal(str)   # 6-значный PIN -> наружу (Supabase / бот)

    def __init__(self):
        super().__init__()
        self.settings = QSettings("CNTRL", "GamesAgent")   # запоминаем статус привязки
        self.linked = self.settings.value("linked", False, type=bool)
        self._game: str | None = None
        self._started: datetime | None = None
        self._quitting = False

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

        self.clock = QTimer(self, interval=1000)   # живой таймер сессии
        self.clock.timeout.connect(self._tick); self.clock.start()

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
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    app.setQuitOnLastWindowClosed(False)       # процесс живёт, пока есть трей
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("[WARN] Системный трей недоступен")

    win = MainWindow()

    # --- ЗАГЛУШКА привязки: замени на запрос к Supabase (в отдельном потоке) ---
    def fake_link(pin: str):
        QTimer.singleShot(1200, lambda: win.set_linked(True) if pin != "000000"
                          else win.show_link_error("Неверный или просроченный PIN"))
    win.pin_submitted.connect(fake_link)

    if "--demo" in sys.argv:                   # имитация игровой сессии
        win.set_activity("Counter-Strike 2", datetime.now() - timedelta(minutes=42))

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()