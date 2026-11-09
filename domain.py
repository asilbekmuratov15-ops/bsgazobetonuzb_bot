import csv
import io
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from pydantic import BaseModel, Field


class Item(BaseModel):
    name: str = ''
    item_code: str = ''
    unit: str = ''
    quantity: Decimal | None = Field(default=None, gt=0)
    price: Decimal | None = Field(default=None, ge=0)
    amount: Decimal | None = Field(default=None, ge=0)


class Invoice(BaseModel):
    document_date: date | None = None
    number: str = ''
    incoming_number: str = ''
    incoming_date: date | None = None
    supplier: str = ''
    source_supplier: str = ''
    supplier_inn: str = ''
    recipient: str = ''
    contract: str = ''
    currency: str = 'UZS'
    warehouse: str = ''
    vat: str = 'Без НДС'
    responsible: str = ''
    exchange: str = ''
    power_of_attorney: str = ''
    customs: str = ''
    contract_ta: str = ''
    security_approved: str = ''
    last_modified: str = ''
    comment: str = ''
    total: Decimal | None = Field(default=None, ge=0)
    items: list[Item] = Field(default_factory=list, max_length=200)
    warnings: list[str] = Field(default_factory=list)


def problems(inv: Invoice) -> list[str]:
    errors = []
    for field in ('document_date', 'supplier', 'warehouse', 'contract'):
        if not getattr(inv, field):
            errors.append(f'{field}: to‘ldirilmagan')
    if inv.total is None:
        errors.append('total: hujjat jami kiritilmagan')
    if not inv.items:
        errors.append('Tovarlar yo‘q')
    total = Decimal(0)
    for n, item in enumerate(inv.items, 1):
        if not item.name or not item.unit:
            errors.append(f'{n}: tovar nomi yoki birligi yo‘q')
        if item.quantity is None or item.price is None or item.amount is None:
            errors.append(f'{n}: miqdor/narx/summa aniqlanmagan')
            continue
        expected = (item.quantity * item.price).quantize(Decimal('.01'))
        if abs(expected - item.amount) > Decimal('.01'):
            errors.append(f'{n}: miqdor × narx ({expected}) summa ({item.amount}) bilan mos emas')
        total += item.amount
    if inv.total is not None and abs(total - inv.total) > Decimal('.01'):
        errors.append(f'Qatorlar jami {total}, hujjat jami {inv.total}')
    return errors


def export_csv(documents, profile_path=Path(__file__).with_name('csv_profile.json')):
    profile = json.loads(Path(profile_path).read_text(encoding='utf-8'))
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, delimiter=profile['delimiter'])
    writer.writerow(profile['columns'].values())
    def safe(value):
        if isinstance(value, Decimal):
            return format(value, 'f').replace('.', profile['decimal_separator'])
        if isinstance(value, date):
            return value.strftime('%d.%m.%Y')
        value = str(value or '')
        return "'" + value if value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else value
    for doc_id, inv in documents:
        if problems(inv):
            raise ValueError('Tasdiqlanmagan yoki xatoli hujjat')
        for n, item in enumerate(inv.items, 1):
            row = {**inv.model_dump(), **item.model_dump(), 'document_id': doc_id,
                   'line': n, 'document_total': inv.total, 'currency_total': inv.total}
            writer.writerow(safe(row.get(k)) for k in profile['columns'])
    return stream.getvalue().encode(profile['encoding'])
