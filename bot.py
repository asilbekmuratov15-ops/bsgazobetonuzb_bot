import asyncio
import hashlib
import io
import logging
import os
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from domain import Invoice, Item, problems, export_csv
from storage import Store
from ocr import extract

load_dotenv(Path(__file__).with_name('.env'))
dp = Dispatcher()
allowed = {int(x.strip()) for x in os.getenv('ALLOWED_USER_IDS','').split(',') if x.strip()}
store = Store(os.getenv('DATABASE_URL',''))
gate = asyncio.Semaphore(2)


@dp.message.outer_middleware()
async def access(handler, event, data):
    if event.chat.type != 'private' or not event.from_user or event.from_user.id not in allowed:
        await event.answer('Kirish yopiq. Administrator ALLOWED_USER_IDS ro‘yxatiga Telegram ID raqamingizni qo‘shishi kerak.')
        return
    try:
        return await handler(event, data)
    except (ValueError, IndexError, KeyError) as exc:
        await event.answer(('Xato: ' + str(exc))[:3000])
    except Exception:
        logging.error('So‘rov bajarilmadi; maxfiy ma’lumotlar logga yozilmadi')
        await event.answer('Xizmatda xato yuz berdi. Bazaga ulanish va API sozlamalarini tekshiring, keyin qayta urinib ko‘ring.')


HELP = '''Nakladnoy rasmini yuboring (JPEG/PNG, 10 MB gacha).
Rasm Groq xizmatiga o‘qish uchun yuboriladi.
/list — oxirgi hujjatlar
/show ID — ko‘rish
/set ID maydon qiymat — sarlavhani tuzatish
Misol: /set 1 document_date 2026-11-03
/set 1 supplier Элмуродов Сарвар (снабженец)
/set 1 warehouse склад снабжения
/set 1 contract Договор № 01.07
/set 1 total 720000
/row ID QATOR maydon qiymat — tovarni tuzatish
Misol: /row 1 1 quantity 2
Tovar maydonlari: name, item_code, unit, quantity, price, amount
/add ID nom | birlik | miqdor | narx | summa — qator qo‘shish
/delete ID QATOR — qator o‘chirish
/approve ID — tekshirib tasdiqlash
/csv ID — bitta tasdiqlangan hujjat
/batch YYYY-MM-DD — shu sanadagi barcha tasdiqlangan hujjatlar
Sana ISO formatda, sonlarda nuqta ishlating. Qiymatni tozalash uchun - yozing.
Har rasm alohida hujjat. Ko‘p sahifali hujjatni bitta rasm qilib yuboring.'''


async def show(message, doc_id):
    inv, status = await asyncio.to_thread(store.get,message.from_user.id,doc_id)
    lines = [f'Hujjat #{doc_id} [{status}]', inv.model_dump_json(indent=2),
             'Tekshiruv: ' + ('; '.join(problems(inv)) or 'summalar mos'),
             f'Tekshirgach: /approve {doc_id}']
    text = '\n'.join(lines)
    for start in range(0,len(text),3500):
        await message.answer(text[start:start+3500])


@dp.message(Command('start','help'))
async def help_cmd(m: Message):
    await m.answer(HELP)


@dp.message(Command('show'))
async def show_cmd(m: Message):
    await show(m,int(m.text.split()[1]))


@dp.message(Command('list'))
async def list_cmd(m: Message):
    rows = await asyncio.to_thread(store.recent,m.from_user.id)
    await m.answer('\n'.join(f"#{r['id']} {r['status']} | {r['data'].get('document_date')} | {r['data'].get('supplier')}" for r in rows) or 'Hujjatlar yo‘q')


@dp.message(Command('set','row'))
async def edit_cmd(m: Message):
    row_mode = m.text.split()[0].split('@')[0] == '/row'
    parts = m.text.split(maxsplit=4 if row_mode else 3)
    doc_id = int(parts[1])
    inv, _ = await asyncio.to_thread(store.get,m.from_user.id,doc_id)
    data = inv.model_dump(mode='json')
    target = data['items'][int(parts[2])-1] if row_mode else data
    if row_mode and int(parts[2]) < 1:
        raise ValueError('Qator 1 dan boshlanadi')
    field, value = parts[-2:]
    permitted = set(target) - {'items','warnings'}
    if field not in permitted:
        raise ValueError('Maydonlar: ' + ', '.join(sorted(permitted)))
    target[field] = (None if field in {'quantity','price','amount','total','document_date','incoming_date'} else '') if value == '-' else value
    inv = Invoice.model_validate(data)
    await asyncio.to_thread(store.update,m.from_user.id,doc_id,inv)
    await show(m,doc_id)


@dp.message(Command('approve'))
async def approve_cmd(m: Message):
    doc_id = int(m.text.split()[1])
    inv, _ = await asyncio.to_thread(store.get,m.from_user.id,doc_id)
    errors = problems(inv)
    if errors:
        await m.answer('Avval tuzating:\n' + '\n'.join(errors))
        return
    await asyncio.to_thread(store.approve,m.from_user.id,doc_id)
    await m.answer(f'Tasdiqlandi. /csv {doc_id}')


@dp.message(Command('add','delete'))
async def rows_cmd(m: Message):
    command, ident, value = m.text.split(maxsplit=2)
    doc_id = int(ident)
    inv, _ = await asyncio.to_thread(store.get,m.from_user.id,doc_id)
    if command.split('@')[0] == '/add':
        values = [v.strip() for v in value.split('|')]
        if len(values) != 5:
            raise ValueError('/add ID nom | birlik | miqdor | narx | summa')
        inv.items.append(Item(name=values[0],unit=values[1],quantity=values[2],price=values[3],amount=values[4]))
    else:
        index = int(value)
        if index < 1:
            raise ValueError('Qator 1 dan boshlanadi')
        inv.items.pop(index-1)
    inv = Invoice.model_validate(inv.model_dump())
    await asyncio.to_thread(store.update,m.from_user.id,doc_id,inv)
    await show(m,doc_id)


@dp.message(Command('csv','batch'))
async def csv_cmd(m: Message):
    command, arg = m.text.split(maxsplit=1)
    if command.split('@')[0] == '/batch':
        day = date.fromisoformat(arg).isoformat()
        docs = await asyncio.to_thread(store.approved,m.from_user.id,day)
        filename = f'nakladnoy_{day}.csv'
    else:
        doc_id = int(arg)
        inv, status = await asyncio.to_thread(store.get,m.from_user.id,doc_id)
        if status != 'approved':
            raise ValueError('Avval /approve bilan tasdiqlang')
        docs, filename = [(doc_id,inv)], f'nakladnoy_{doc_id}.csv'
    if not docs:
        raise ValueError('Tasdiqlangan hujjat yo‘q')
    await m.answer_document(BufferedInputFile(export_csv(docs),filename=filename))


@dp.message(F.photo | F.document)
async def image_cmd(m: Message, bot: Bot):
    obj = m.photo[-1] if m.photo else m.document
    if obj.file_size and obj.file_size > 10 * 1024 * 1024:
        raise ValueError('Rasm 10 MB dan katta')
    await m.answer('Rasm qabul qilindi, o‘qilmoqda…')
    async with gate:
        stream = io.BytesIO()
        await bot.download(obj,destination=stream)
        data = stream.getvalue()
        if len(data) > 10 * 1024 * 1024:
            raise ValueError('Rasm juda katta')
        with Image.open(io.BytesIO(data)) as img:
            if img.format not in {'JPEG','PNG'}:
                raise ValueError('Faqat JPEG/PNG yuboring')
            mime = 'image/jpeg' if img.format == 'JPEG' else 'image/png'
            img.verify()
        inv = await extract(data,mime,os.environ['GROQ_API_KEY'],os.getenv('GROQ_MODEL','qwen/qwen3.8-27b'))
        for field, env in [('warehouse','DEFAULT_WAREHOUSE'),('contract','DEFAULT_CONTRACT'),('responsible','DEFAULT_RESPONSIBLE')]:
            if not getattr(inv,field):
                setattr(inv,field,os.getenv(env,''))
        doc_id, duplicate = await asyncio.to_thread(store.add,m.from_user.id,hashlib.sha256(data).hexdigest(),inv)
    if duplicate:
        await m.answer('Bu rasm avval kiritilgan. Oldingi hujjat ochildi.')
    await show(m,doc_id)


async def main():
    for key in ('TELEGRAM_BOT_TOKEN','GROQ_API_KEY','DATABASE_URL','ALLOWED_USER_IDS'):
        if not os.getenv(key):
            raise SystemExit(f'.env ichida {key} ni kiriting')
    for attempt in range(6):
        try:
            await asyncio.to_thread(store.init)
            break
        except Exception:
            if attempt == 5:
                raise SystemExit('PostgreSQL bilan ulanish o‘rnatilmadi. DATABASE_URL va baza holatini tekshiring.')
            logging.warning('PostgreSQL kutilmoqda (%s/6)', attempt + 1)
            await asyncio.sleep(3)
    async with Bot(os.environ['TELEGRAM_BOT_TOKEN']) as bot:
        me = await bot.get_me()
        print(f'Bot ishga tushdi: @{me.username}', flush=True)
        await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())
