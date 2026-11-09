"""Dependencies shared by handlers through aiogram's dependency injection."""

import asyncio
from dataclasses import dataclass, field

from app.config import Settings
from app.db.repository import Store


@dataclass
class BotContext:
    settings: Settings
    store: Store
    gate: asyncio.Semaphore = field(default_factory=lambda: asyncio.Semaphore(2))
