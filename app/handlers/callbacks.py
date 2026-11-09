import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery

from app.context import BotContext
from app.services.counterparties import apply_party
from app.services.csv_export import export_csv
from app.services.validation import problems
from app.states import PartyFlow
from app.ui.views import show

router = Router(name="callbacks")


@router.callback_query(F.data.startswith("inv:"))
async def invoice_action(cb: CallbackQuery, state: FSMContext, ctx: BotContext):
    await cb.answer()
    parts = cb.data.split(":")
    action, doc_id = (parts[1], int(parts[2]))
    owner = cb.from_user.id
    inv, status = await asyncio.to_thread(ctx.store.get, owner, doc_id)
    m = cb.message
    if action in {"parties", "back"}:
        await state.clear()
        await show(m, doc_id, owner, selecting=action == "parties", ctx=ctx)
    elif action == "page":
        saved = await state.get_data()
        query = saved.get("query", "") if saved.get("doc_id") == doc_id else ""
        await show(
            m, doc_id, owner, selecting=True, query=query, page=max(0, int(parts[3])), ctx=ctx
        )
    elif action in {"search", "new"}:
        await state.set_state(PartyFlow.search if action == "search" else PartyFlow.new)
        await state.update_data(doc_id=doc_id, query="")
        await m.answer(
            "Kontragent nomi yoki INN yozing. To‘xtatish: /bekor"
            if action == "search"
            else "Yozing: INN; 1C dagi aniq nomi; Shartnoma\nMasalan: 123456789; Korxona nomi; Договор № 1\nTo‘xtatish: /bekor"
        )
    elif action == "choose":
        party = await asyncio.to_thread(ctx.store.party, owner, int(parts[3]))
        await apply_party(owner, doc_id, inv, party, ctx=ctx)
        await state.clear()
        await show(m, doc_id, owner, ctx=ctx)
    elif action == "approve":
        errors = problems(inv)
        if errors:
            await m.answer("Avval tuzating:\n" + "\n".join(errors))
            return
        await asyncio.to_thread(ctx.store.approve, owner, doc_id)
        await show(m, doc_id, owner, ctx=ctx)
    elif action == "csv":
        if status != "approved":
            raise ValueError("Avval tasdiqlang")
        await m.answer_document(
            BufferedInputFile(export_csv([(doc_id, inv)]), filename=f"nakladnoy_{doc_id}.csv")
        )
    elif action == "edit":
        await m.answer(
            f"Tuzatish misollari:\n/set {doc_id} document_date 2026-11-03\n/set {doc_id} warehouse склад снабжения\n/set {doc_id} contract Договор № 1\n/set {doc_id} total 720000\n/row {doc_id} 1 name А4 лист\n/row {doc_id} 1 quantity 2\n/row {doc_id} 1 price 250000\n/row {doc_id} 1 amount 500000\nBarcha buyruqlar: /help"
        )
