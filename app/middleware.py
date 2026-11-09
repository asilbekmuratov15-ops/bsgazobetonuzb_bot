import logging

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery


class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        message = event.message if isinstance(event, CallbackQuery) else event
        ctx = data["ctx"]
        if (
            not message
            or message.chat.type != "private"
            or not event.from_user
            or event.from_user.id not in ctx.settings.allowed_user_ids
        ):
            await event.answer(
                "Kirish yopiq. Administrator Telegram ID raqamingizga ruxsat berishi kerak."
            )
            return
        try:
            return await handler(event, data)
        except (ValueError, IndexError, KeyError) as exc:
            await message.answer(("Xato: " + str(exc))[:3000])
        except Exception:
            logging.error("So‘rov bajarilmadi; maxfiy ma’lumotlar logga yozilmadi")
            await message.answer("Xizmatda xato yuz berdi. Keyinroq qayta urinib ko‘ring.")
