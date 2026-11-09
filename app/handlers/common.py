from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.context import BotContext
from app.ui.texts import HELP
from app.ui.views import show

router = Router(name="common")


@router.message(Command("bekor"))
async def cancel_flow(m: Message, state: FSMContext, ctx: BotContext):
    data = await state.get_data()
    await state.clear()
    await m.answer("Bekor qilindi.")
    if data.get("doc_id"):
        await show(m, data["doc_id"], ctx=ctx)


@router.message(Command("start", "help"))
async def help_cmd(m: Message, ctx: BotContext):
    await m.answer(HELP)
