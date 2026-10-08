"""
CNTRL.GAMES — управление идентификацией устройства.

Общий модуль для GUI и session_tracker. Хранит постоянный device_uid,
умеет регистрировать устройство в Supabase и получать его device_id.
"""
import os
import uuid
import logging
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client
from PyQt6.QtCore import QSettings

log = logging.getLogger("device_manager")

# Тот же namespace, что в gui.py — важно для шара QSettings!
SETTINGS_NAMESPACE = ("CNTRL", "GamesAgent")


def get_device_uid() -> str:
    """Постоянный UUID этого ПК (хранится в QSettings, создаётся один раз)."""
    st = QSettings(*SETTINGS_NAMESPACE)
    if not st.contains("device_uid"):
        st.setValue("device_uid", str(uuid.uuid4()))
        st.sync()
    return str(st.value("device_uid"))


def get_supabase_client() -> Optional[Client]:
    """Создаёт клиент Supabase из .env (ищет и в agent/, и в корне)."""
    base = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(base, ".env"))
    load_dotenv(os.path.join(base, "..", ".env"))

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        log.error("SUPABASE_URL / SUPABASE_KEY не найдены в .env")
        return None

    return create_client(url, key)


class DeviceManager:
    """Регистрирует ПК в devices и кеширует device_id."""

    def __init__(self):
        self.device_uid = get_device_uid()
        self.supabase = get_supabase_client()
        self.device_id: Optional[int] = None
        self.parent_telegram_id: Optional[int] = None

    def ensure_device(self) -> Optional[int]:
        """
        Гарантирует, что запись в devices существует.
        Возвращает device_id или None при ошибке.
        """
        if not self.supabase:
            return None

        try:
            res = (
                self.supabase.table("devices")
                .select("id,parent_telegram_id")
                .eq("device_uid", self.device_uid)
                .limit(1)
                .execute()
            )

            if res.data:
                self.device_id = res.data[0]["id"]
                self.parent_telegram_id = res.data[0].get("parent_telegram_id")
                log.info("Устройство найдено: device_id=%s", self.device_id)
                return self.device_id

            # Устройства нет — создаём «пустое»
            import platform
            res = (
                self.supabase.table("devices")
                .insert({
                    "device_uid": self.device_uid,
                    "name": platform.node(),
                    "os": platform.platform(),
                    "is_active": True,
                })
                .execute()
            )
            if res.data:
                self.device_id = res.data[0]["id"]
                log.info("Устройство создано: device_id=%s", self.device_id)
                return self.device_id

        except Exception as e:
            log.error("Ошибка ensure_device: %s", e)

        return None

    def refresh_parent(self) -> Optional[int]:
        """Подтягивает parent_telegram_id из БД (после привязки через бота)."""
        if not self.supabase or not self.device_id:
            return None

        try:
            res = (
                self.supabase.table("devices")
                .select("parent_telegram_id")
                .eq("id", self.device_id)
                .limit(1)
                .execute()
            )
            if res.data:
                self.parent_telegram_id = res.data[0].get("parent_telegram_id")
                return self.parent_telegram_id
        except Exception as e:
            log.error("Ошибка refresh_parent: %s", e)

        return None