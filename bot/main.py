"""
CNTRL.GAMES — Telegram bot
Python 3.11+
aiogram 3.x
Supabase
python-dotenv

Установка:
    pip install aiogram supabase python-dotenv

Переменные окружения (.env):
    BOT_TOKEN=your_telegram_bot_token
    SUPABASE_URL=https://xxxx.supabase.co
    SUPABASE_KEY=your_supabase_anon_or_service_key
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
from datetime import datetime, timezone, timedelta
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv
from supabase import Client, create_client


# ============================================================================
# ENVIRONMENT
# ============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Поддерживаем как .env рядом с ботом, так и .env в корне проекта.
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))


BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

PAIRING_CODES_TABLE = "pairing_codes"
DEVICES_TABLE = "devices"
NOW_PLAYING_TABLE = "now_playing"
GAME_SESSIONS_TABLE = "game_sessions"
GAMES_TABLE = "games"

# Максимальное количество сессий, показываемых в истории.
HISTORY_LIMIT = 10

# Сколько минут действует pairing code.
PAIRING_CODE_TTL_MIN = 10


# ============================================================================
# TIMEZONE
# ============================================================================

# Московское время (UTC+3). С 2014 года в РФ нет перехода на летнее время.
MOSCOW_TZ = timezone(timedelta(hours=3))


# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger("cntrl_games_bot")


# ============================================================================
# VALIDATION
# ============================================================================

def validate_environment() -> None:
    """Проверяет обязательные переменные окружения."""

    missing: list[str] = []

    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")

    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")

    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )


validate_environment()


# ============================================================================
# SUPABASE
# ============================================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


# ============================================================================
# BOT & DISPATCHER
# ============================================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
    ),
)

dp = Dispatcher()


# ============================================================================
# KEYBOARDS
# ============================================================================

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📱 Статус сейчас"),
            KeyboardButton(text="📊 История сессий"),
        ],
        [
            KeyboardButton(text="🔗 Привязать устройство"),
        ],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


# ============================================================================
# GENERIC HELPERS
# ============================================================================

async def db_execute(func):
    """Удобная обертка для выполнения Supabase-запросов."""

    return await asyncio.to_thread(func)


def utc_now() -> datetime:
    """Текущее время UTC."""

    return datetime.now(timezone.utc)


def parse_datetime(value: Any) -> datetime | None:
    """
    Преобразует значение Supabase/Postgres timestamp в datetime.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            logger.warning("Unable to parse datetime: %r", value)
            return None
    else:
        logger.warning("Unsupported datetime type: %r", type(value))
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def format_duration(seconds: int | float | None) -> str:
    """Форматирует длительность в человекочитаемый вид."""

    if seconds is None:
        return "0 сек."

    total_seconds = max(0, int(seconds))

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts: list[str] = []

    if hours:
        parts.append(f"{hours} ч.")

    if minutes:
        parts.append(f"{minutes} мин.")

    if seconds or not parts:
        parts.append(f"{seconds} сек.")

    return " ".join(parts)


def format_datetime(dt: datetime | None) -> str:
    """Форматирует timestamp в московское время для Telegram."""

    if dt is None:
        return "неизвестно"

    return dt.astimezone(MOSCOW_TZ).strftime(
        "%d.%m.%Y %H:%M МСК"
    )


def calculate_elapsed(start: datetime | None) -> int:
    """Возвращает количество прошедших секунд."""

    if start is None:
        return 0

    return max(
        0,
        int((utc_now() - start).total_seconds()),
    )


def get_telegram_id(message: Message) -> int | None:
    """Безопасно получает Telegram ID пользователя."""

    if message.from_user is None:
        return None

    return message.from_user.id


def generate_pairing_code() -> str:
    """Уникальный 6-значный код (строка с ведущими нулями)."""
    return f"{random.randint(0, 999_999):06d}"


# ============================================================================
# DATABASE REPOSITORY
# ============================================================================

class DatabaseError(Exception):
    """Ошибка работы с Supabase."""


class Database:
    """
    Репозиторий Supabase.
    """

    def __init__(self, client: Client):
        self.client = client

    # ------------------------------------------------------------------------
    # DEVICE / PARENT
    # ------------------------------------------------------------------------

    async def get_parent_devices(
        self,
        telegram_id: int,
    ) -> list[dict[str, Any]]:
        """Устройства, привязанные к Telegram ID родителя."""

        try:
            response = await db_execute(
                lambda: (
                    self.client
                    .table(DEVICES_TABLE)
                    .select("id,name,parent_telegram_id")
                    .eq("parent_telegram_id", telegram_id)
                    .execute()
                )
            )

            return response.data or []

        except Exception as exc:
            logger.exception(
                "Failed to load devices for parent %s",
                telegram_id,
            )
            raise DatabaseError(
                "Failed to load parent devices"
            ) from exc

    async def create_pairing_code(
        self,
        telegram_id: int,
    ) -> str | None:
        """
        Генерирует 6-значный PIN и сохраняет его в pairing_codes.
        Возвращает код или None при ошибке.
        """

        now = utc_now()
        expires_at = now + timedelta(minutes=PAIRING_CODE_TTL_MIN)

        # Пробуем до 5 раз, если случится коллизия (маловероятно, но код уникален)
        for _ in range(5):
            code = generate_pairing_code()
            try:
                response = await db_execute(
                    lambda: (
                        self.client
                        .table(PAIRING_CODES_TABLE)
                        .insert({
                            "code": code,
                            "parent_telegram_id": telegram_id,
                            "used": False,
                            "expires_at": expires_at.isoformat(),
                        })
                        .execute()
                    )
                )
            except Exception as exc:
                # Проверим, не коллизия ли это (unique violation).
                msg = str(exc)
                if "duplicate" in msg.lower() or "unique" in msg.lower():
                    continue  # пробуем ещё раз с новым кодом
                logger.exception("Failed to create pairing code")
                return None

            if response.data:
                return code

        logger.error("Не удалось сгенерировать уникальный pairing code")
        return None

    # ------------------------------------------------------------------------
    # NOW PLAYING
    # ------------------------------------------------------------------------

    async def get_now_playing(
        self,
        device_id: Any,
    ) -> dict[str, Any] | None:
        """Текущий статус устройства."""

        try:
            response = await db_execute(
                lambda: (
                    self.client
                    .table(NOW_PLAYING_TABLE)
                    .select(
                        "id,device_id,game_name,session_start,updated_at"
                    )
                    .eq("device_id", device_id)
                    .limit(1)
                    .execute()
                )
            )

            if not response.data:
                return None

            return response.data[0]

        except Exception as exc:
            logger.exception(
                "Failed to load now_playing for device %s",
                device_id,
            )
            raise DatabaseError(
                "Failed to load current status"
            ) from exc

    # ------------------------------------------------------------------------
    # GAME SESSIONS
    # ------------------------------------------------------------------------

    async def get_game_sessions(
        self,
        device_id: Any,
        limit: int = HISTORY_LIMIT,
    ) -> list[dict[str, Any]]:
        """Последние игровые сессии устройства."""

        try:
            response = await db_execute(
                lambda: (
                    self.client
                    .table(GAME_SESSIONS_TABLE)
                    .select(
                        "id,game_id,started_at,duration_seconds,"
                        "games(id,name)"
                    )
                    .eq("device_id", device_id)
                    .order(
                        "started_at",
                        desc=True,
                    )
                    .limit(limit)
                    .execute()
                )
            )

            return response.data or []

        except Exception as exc:
            logger.exception(
                "Failed to load game sessions for device %s",
                device_id,
            )
            raise DatabaseError(
                "Failed to load game sessions"
            ) from exc


# ============================================================================
# GLOBAL DATABASE INSTANCE
# ============================================================================

db = Database(supabase)


# ============================================================================
# UI HELPERS
# ============================================================================

async def get_single_device_for_user(
    telegram_id: int,
) -> dict[str, Any] | None:
    """
    Возвращает первое устройство пользователя.
    """

    devices = await db.get_parent_devices(telegram_id)

    if not devices:
        return None

    return devices[0]


# ============================================================================
# /START
# ============================================================================

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик /start."""

    first_name = (
        message.from_user.first_name
        if message.from_user
        else "родитель"
    )

    text = (
        f"👋 Привет, {first_name}!\n\n"
        "Добро пожаловать в <b>CNTRL.GAMES</b>.\n\n"
        "Сервис помогает родителям понимать, "
        "как ребенок использует компьютер: "
        "какие игры запускаются, сколько длится игровая сессия "
        "и чем ребенок занят прямо сейчас.\n\n"
        "Выберите действие ниже:"
    )

    await message.answer(
        text,
        reply_markup=MAIN_KEYBOARD,
    )


# ============================================================================
# PAIR DEVICE
# ============================================================================

@dp.message(F.text == "🔗 Привязать устройство")
async def start_pairing(message: Message) -> None:
    """Генерирует PIN и отправляет его родителю."""

    telegram_id = get_telegram_id(message)

    if telegram_id is None:
        await message.answer(
            "Не удалось определить Telegram ID пользователя."
        )
        return

    try:
        code = await db.create_pairing_code(telegram_id)

    except DatabaseError:
        await message.answer(
            "⚠️ Не удалось связаться с сервером.\n"
            "Попробуйте позже."
        )
        return

    if not code:
        await message.answer(
            "⚠️ Не удалось создать код привязки.\n"
            "Попробуйте позже."
        )
        return

    await message.answer(
        "🔗 <b>Код для привязки устройства</b>\n\n"
        f"Код: <code>{code}</code>\n\n"
        f"⚠️ Код действует {PAIRING_CODE_TTL_MIN} минут.\n\n"
        "<b>Что делать дальше:</b>\n"
        "1. Откройте приложение <b>CNTRL.GAMES</b> "
        "на компьютере ребёнка.\n"
        "2. Введите этот код в поле «Привязка к Telegram».\n"
        "3. Нажмите «Привязать ПК».\n\n"
        "После этого я смогу показывать вам активность ребёнка."
    )


# ============================================================================
# CURRENT STATUS
# ============================================================================

@dp.message(F.text == "📱 Статус сейчас")
async def current_status(message: Message) -> None:
    """Показывает текущую активность ребенка."""

    telegram_id = get_telegram_id(message)

    if telegram_id is None:
        await message.answer(
            "Не удалось определить Telegram ID пользователя."
        )
        return

    try:
        device = await get_single_device_for_user(telegram_id)

    except DatabaseError:
        await message.answer(
            "⚠️ Не удалось получить данные устройства.\n"
            "Попробуйте позже."
        )
        return

    if device is None:
        await message.answer(
            "🔗 <b>Устройство не привязано.</b>\n\n"
            "Сначала нажмите «🔗 Привязать устройство» "
            "и введите полученный код на компьютере ребёнка."
        )
        return

    device_id = device["id"]

    try:
        now_playing = await db.get_now_playing(device_id)

    except DatabaseError:
        await message.answer(
            "⚠️ Не удалось получить текущий статус.\n"
            "Попробуйте через несколько секунд."
        )
        return

    if not now_playing:
        await message.answer(
            "💤 <b>Активности сейчас нет.</b>\n\n"
            "Компьютер свободен или выключен."
        )
        return

    game_name = now_playing.get("game_name")
    session_start = parse_datetime(
        now_playing.get("session_start")
    )

    if not game_name or not session_start:
        await message.answer(
            "💤 <b>Активности сейчас нет.</b>\n\n"
            "Компьютер свободен или выключен."
        )
        return

    elapsed = calculate_elapsed(session_start)

    device_name = device.get("name")

    device_line = (
        f"💻 Устройство: <b>{device_name}</b>\n"
        if device_name
        else ""
    )

    await message.answer(
        "🎮 <b>Ребенок сейчас играет</b>\n\n"
        f"{device_line}"
        f"🎯 Игра: <b>{game_name}</b>\n"
        f"🕐 Начало: <b>{format_datetime(session_start)}</b>\n"
        f"⏱ Прошло: <b>{format_duration(elapsed)}</b>"
    )


# ============================================================================
# SESSION HISTORY
# ============================================================================

@dp.message(F.text == "📊 История сессий")
async def session_history(message: Message) -> None:
    """Показывает последние игровые сессии."""

    telegram_id = get_telegram_id(message)

    if telegram_id is None:
        await message.answer(
            "Не удалось определить Telegram ID пользователя."
        )
        return

    try:
        device = await get_single_device_for_user(telegram_id)

    except DatabaseError:
        await message.answer(
            "⚠️ Не удалось получить данные устройства.\n"
            "Попробуйте позже."
        )
        return

    if device is None:
        await message.answer(
            "🔗 <b>Устройство не привязано.</b>\n\n"
            "Сначала привяжите компьютер ребенка."
        )
        return

    try:
        sessions = await db.get_game_sessions(
            device_id=device["id"],
            limit=HISTORY_LIMIT,
        )

    except DatabaseError:
        await message.answer(
            "⚠️ Не удалось загрузить историю сессий.\n"
            "Попробуйте позже."
        )
        return

    if not sessions:
        await message.answer(
            "📊 <b>История сессий пока пуста.</b>\n\n"
            "Когда ребенок запустит игру, "
            "здесь появится информация о сессии."
        )
        return

    lines = [
        "📊 <b>Последние игровые сессии</b>",
        "",
    ]

    for index, session in enumerate(sessions, start=1):
        started_at = parse_datetime(
            session.get("started_at")
        )

        duration = session.get("duration_seconds") or 0

        game = session.get("games")

        if isinstance(game, list):
            game = game[0] if game else None

        if isinstance(game, dict):
            game_name = game.get("name") or "Неизвестная игра"
        else:
            game_name = "Неизвестная игра"

        lines.append(
            f"<b>{index}. {game_name}</b>"
        )
        lines.append(
            f"📅 {format_datetime(started_at)}"
        )
        lines.append(
            f"⏱ {format_duration(duration)}"
        )

        if index != len(sessions):
            lines.append("")

    await message.answer(
        "\n".join(lines)
    )


# ============================================================================
# UNKNOWN TEXT
# ============================================================================

@dp.message()
async def unknown_message(message: Message) -> None:
    """Обработчик неизвестных сообщений."""

    await message.answer(
        "Выберите действие с помощью кнопок ниже.",
        reply_markup=MAIN_KEYBOARD,
    )


# ============================================================================
# ERROR HANDLER
# ============================================================================

@dp.errors()
async def global_error_handler(
    event: Any,
) -> bool:
    """Глобальный обработчик ошибок aiogram."""

    logger.exception(
        "Unhandled Telegram bot error: %s",
        event,
    )

    return True


# ============================================================================
# BOT STARTUP
# ============================================================================

async def main() -> None:
    """Запускает Telegram polling."""

    try:
        me = await bot.get_me()

        logger.info(
            "Starting CNTRL.GAMES bot: @%s (id=%s)",
            me.username,
            me.id,
        )

        await bot.delete_webhook(
            drop_pending_updates=True,
        )

        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )

    except asyncio.CancelledError:
        logger.info("Bot polling cancelled")
        raise

    except Exception:
        logger.exception("Fatal bot error")
        raise

    finally:
        await bot.session.close()
        logger.info("Bot stopped")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("CNTRL.GAMES bot stopped by user")

    except Exception:
        logger.exception("CNTRL.GAMES bot terminated")