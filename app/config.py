"""Environment settings. Importing this module never reads credentials."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = field(default="", repr=False)
    groq_api_key: str = field(default="", repr=False)
    database_url: str = field(default="", repr=False)
    allowed_user_ids: frozenset[int] = frozenset()
    groq_model: str = "qwen/qwen3.8-27b"
    default_warehouse: str = ""
    default_contract: str = ""
    default_responsible: str = ""

    @classmethod
    def load(cls):
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        try:
            allowed = frozenset(
                int(v.strip()) for v in os.getenv("ALLOWED_USER_IDS", "").split(",") if v.strip()
            )
        except ValueError:
            raise ValueError(
                "ALLOWED_USER_IDS faqat raqamli Telegram IDlardan iborat bo‘lsin."
            ) from None
        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            allowed_user_ids=allowed,
            groq_model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
            default_warehouse=os.getenv("DEFAULT_WAREHOUSE", ""),
            default_contract=os.getenv("DEFAULT_CONTRACT", ""),
            default_responsible=os.getenv("DEFAULT_RESPONSIBLE", ""),
        )

    def validate(self):
        for key, value in (
            ("TELEGRAM_BOT_TOKEN", self.telegram_bot_token),
            ("GROQ_API_KEY", self.groq_api_key),
            ("DATABASE_URL", self.database_url),
            ("ALLOWED_USER_IDS", self.allowed_user_ids),
        ):
            if not value:
                raise ValueError(f"{key} ni sozlamalarda kiriting.")
