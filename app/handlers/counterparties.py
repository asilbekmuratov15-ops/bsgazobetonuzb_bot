import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.context import BotContext
from app.services.counterparties import apply_party
from app.states import PartyFlow
from app.ui.views import show

router = Router(name="counterparties")


@router.message(PartyFlow.search, F.text)
async def party_search(m: Message, state: FSMContext, ctx: BotContext):
    data = await state.get_data()
    query = m.text.strip()[:100]
    await state.update_data(query=query)
    await state.set_state(None)
    await show(m, data["doc_id"], selecting=True, query=query, ctx=ctx)


@router.message(PartyFlow.new, F.text)
async def party_new(m: Message, state: FSMContext, ctx: BotContext):
    data = await state.get_data()
    values = [v.strip() for v in m.text.split(";", 2)]
    if (
        len(values) != 3
        or not all(values)
        or (not values[0].isascii())
        or (not values[0].isdigit())
        or (len(values[0]) != 9)
    ):
        await m.answer("Format: 9 xonali INN; 1C dagi aniq nomi; Shartnoma\nTo‘xtatish: /bekor")
        return
    if any((len(v) > 500 for v in values)):
        await m.answer("Har bir maydon 500 belgidan oshmasin.")
        return
    owner, doc_id = (m.from_user.id, data["doc_id"])
    inv, _ = await asyncio.to_thread(ctx.store.get, owner, doc_id)
    party = await asyncio.to_thread(ctx.store.save_party, owner, values[1], values[0], values[2])
    await apply_party(owner, doc_id, inv, party, ctx=ctx)
    await state.clear()
    await m.answer("Kontragent saqlandi va hujjatga tanlandi.")
    await show(m, doc_id, ctx=ctx)
