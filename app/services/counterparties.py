import asyncio

from app.context import BotContext


async def apply_party(owner, doc_id, inv, party, *, ctx: BotContext):
    if not inv.source_supplier:
        inv.source_supplier = inv.supplier
    inv.supplier, inv.supplier_inn, inv.contract = (party["name"], party["inn"], party["contract"])
    await asyncio.to_thread(ctx.store.update, owner, doc_id, inv)
