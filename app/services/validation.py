from decimal import Decimal

from app.models.invoice import Invoice


def problems(inv: Invoice) -> list[str]:
    errors = []
    for field, label in (
        ("document_date", "Sana"),
        ("supplier", "Kontragent"),
        ("warehouse", "Ombor"),
        ("contract", "Shartnoma"),
    ):
        if not getattr(inv, field):
            errors.append(f"{label}: to‘ldirilmagan")
    if inv.total is None:
        errors.append("Hujjat jami kiritilmagan")
    if not inv.items:
        errors.append("Tovarlar yo‘q")
    total = Decimal(0)
    for n, item in enumerate(inv.items, 1):
        if not item.name or not item.unit:
            errors.append(f"{n}: tovar nomi yoki birligi yo‘q")
        if item.quantity is None or item.price is None or item.amount is None:
            errors.append(f"{n}: miqdor/narx/summa aniqlanmagan")
            continue
        expected = (item.quantity * item.price).quantize(Decimal(".01"))
        if abs(expected - item.amount) > Decimal(".01"):
            errors.append(f"{n}: miqdor × narx ({expected}) summa ({item.amount}) bilan mos emas")
        total += item.amount
    if inv.total is not None and abs(total - inv.total) > Decimal(".01"):
        errors.append(f"Qatorlar jami {total}, hujjat jami {inv.total}")
    return errors
