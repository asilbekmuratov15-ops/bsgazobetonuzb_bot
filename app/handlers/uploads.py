import asyncio
import hashlib
import io

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from PIL import Image

from app.context import BotContext
from app.services.groq_ocr import extract
from app.ui.views import show

router = Router(name="uploads")


@router.message(F.photo | F.document)
async def image_cmd(m: Message, bot: Bot, state: FSMContext, ctx: BotContext):
    await state.clear()
    obj = m.photo[-1] if m.photo else m.document
    if obj.file_size and obj.file_size > 10 * 1024 * 1024:
        raise ValueError("Rasm 10 MB dan katta")
    await m.answer("Rasm qabul qilindi, o‘qilmoqda…")
    async with ctx.gate:
        stream = io.BytesIO()
        await bot.download(obj, destination=stream)
        data = stream.getvalue()
        if len(data) > 10 * 1024 * 1024:
            raise ValueError("Rasm juda katta")
        with Image.open(io.BytesIO(data)) as img:
            if img.format not in {"JPEG", "PNG"}:
                raise ValueError("Faqat JPEG/PNG yuboring")
            mime = "image/jpeg" if img.format == "JPEG" else "image/png"
            img.verify()
        inv = await extract(data, mime, ctx.settings.groq_api_key, ctx.settings.groq_model)
        inv.source_supplier = inv.supplier
        for field, env in [
            ("warehouse", "default_warehouse"),
            ("contract", "default_contract"),
            ("responsible", "default_responsible"),
        ]:
            if not getattr(inv, field):
                setattr(inv, field, getattr(ctx.settings, env))
        doc_id, duplicate = await asyncio.to_thread(
            ctx.store.add, m.from_user.id, hashlib.sha256(data).hexdigest(), inv
        )
    if duplicate:
        await m.answer("Bu rasm avval kiritilgan. Oldingi hujjat ochildi.")
    await show(m, doc_id, selecting=True, reply_to=True, ctx=ctx)
