import asyncio
from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

from app.context import BotContext
from app.models.invoice import Invoice, Item
from app.services.csv_export import export_csv
from app.services.validation import problems
from app.ui.views import show

router = Router(name="documents")


@router.message(Command("show"))
async def show_cmd(m: Message, ctx: BotContext):
    await show(m, int(m.text.split()[1]), ctx=ctx)


@router.message(Command("list"))
async def list_cmd(m: Message, ctx: BotContext):
    rows = await asyncio.to_thread(ctx.store.recent, m.from_user.id)
    await m.answer(
        "\n".join(
            (
                f"#{r['id']} {r['status']} | {r['data'].get('document_date')} | {r['data'].get('supplier')}"
                for r in rows
            )
        )
        or "Hujjatlar yo‘q"
    )


@router.message(Command("set", "row"))
async def edit_cmd(m: Message, ctx: BotContext):
    row_mode = m.text.split()[0].split("@")[0] == "/row"
    parts = m.text.split(maxsplit=4 if row_mode else 3)
    doc_id = int(parts[1])
    inv, _ = await asyncio.to_thread(ctx.store.get, m.from_user.id, doc_id)
    data = inv.model_dump(mode="json")
    target = data["items"][int(parts[2]) - 1] if row_mode else data
    if row_mode and int(parts[2]) < 1:
        raise ValueError("Qator 1 dan boshlanadi")
    field, value = parts[-2:]
    permitted = set(target) - {"items", "warnings"}
    if field not in permitted:
        raise ValueError("Maydonlar: " + ", ".join(sorted(permitted)))
    target[field] = (
        (
            None
            if field in {"quantity", "price", "amount", "total", "document_date", "incoming_date"}
            else ""
        )
        if value == "-"
        else value
    )
    inv = Invoice.model_validate(data)
    await asyncio.to_thread(ctx.store.update, m.from_user.id, doc_id, inv)
    await show(m, doc_id, ctx=ctx)


@router.message(Command("approve"))
async def approve_cmd(m: Message, ctx: BotContext):
    doc_id = int(m.text.split()[1])
    inv, _ = await asyncio.to_thread(ctx.store.get, m.from_user.id, doc_id)
    errors = problems(inv)
    if errors:
        await m.answer("Avval tuzating:\n" + "\n".join(errors))
        return
    await asyncio.to_thread(ctx.store.approve, m.from_user.id, doc_id)
    await show(m, doc_id, ctx=ctx)


@router.message(Command("add", "delete"))
async def rows_cmd(m: Message, ctx: BotContext):
    command, ident, value = m.text.split(maxsplit=2)
    doc_id = int(ident)
    inv, _ = await asyncio.to_thread(ctx.store.get, m.from_user.id, doc_id)
    if command.split("@")[0] == "/add":
        values = [v.strip() for v in value.split("|")]
        if len(values) != 5:
            raise ValueError("/add ID nom | birlik | miqdor | narx | summa")
        inv.items.append(
            Item(
                name=values[0],
                unit=values[1],
                quantity=values[2],
                price=values[3],
                amount=values[4],
            )
        )
    else:
        index = int(value)
        if index < 1:
            raise ValueError("Qator 1 dan boshlanadi")
        inv.items.pop(index - 1)
    inv = Invoice.model_validate(inv.model_dump())
    await asyncio.to_thread(ctx.store.update, m.from_user.id, doc_id, inv)
    await show(m, doc_id, ctx=ctx)


@router.message(Command("csv", "batch"))
async def csv_cmd(m: Message, ctx: BotContext):
    command, arg = m.text.split(maxsplit=1)
    if command.split("@")[0] == "/batch":
        day = date.fromisoformat(arg).isoformat()
        docs = await asyncio.to_thread(ctx.store.approved, m.from_user.id, day)
        filename = f"nakladnoy_{day}.csv"
    else:
        doc_id = int(arg)
        inv, status = await asyncio.to_thread(ctx.store.get, m.from_user.id, doc_id)
        if status != "approved":
            raise ValueError("Avval /approve bilan tasdiqlang")
        docs, filename = ([(doc_id, inv)], f"nakladnoy_{doc_id}.csv")
    if not docs:
        raise ValueError("Tasdiqlangan hujjat yo‘q")
    await m.answer_document(BufferedInputFile(export_csv(docs), filename=filename))
