import asyncio

from aiogram.types import ReplyParameters

from app.context import BotContext
from app.ui.formatters import chunks, summary
from app.ui.keyboards import actions, party_buttons


async def show(
    message,
    doc_id,
    owner=None,
    selecting=False,
    query="",
    page=0,
    reply_to=False,
    *,
    ctx: BotContext,
):
    owner = owner if owner is not None else message.from_user.id
    inv, status = await asyncio.to_thread(ctx.store.get, owner, doc_id)
    keyboard = actions(doc_id, status == "approved")
    text = summary(doc_id, inv, status)
    if selecting:
        await asyncio.to_thread(ctx.store.seed_parties, owner)
        parties = await asyncio.to_thread(ctx.store.parties, owner, query, page)
        keyboard = party_buttons(doc_id, parties[:5], page, len(parties) > 5)
        if not parties:
            text += "\n\nKontragent topilmadi. Qidirish yoki Yangi tugmasidan foydalaning."
    parts = list(chunks(text))
    for n, text in enumerate(parts):
        await message.answer(
            text,
            reply_markup=keyboard if n == len(parts) - 1 else None,
            reply_parameters=ReplyParameters(message_id=message.message_id)
            if reply_to and n == 0
            else None,
        )
