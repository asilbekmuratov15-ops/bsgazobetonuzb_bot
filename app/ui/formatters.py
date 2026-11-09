from decimal import Decimal

from app.models.invoice import Invoice
from app.services.validation import problems


def number(value):
    if value is None:
        return "—"
    return _number(value)


def _number(value):
    result = format(Decimal(value), ",f").replace(",", " ")
    return result.rstrip("0").rstrip(".") if "." in result else result


def summary(doc_id: int, inv: Invoice, status: str):
    lines = [
        f"Nakladnoy #{doc_id} · " + ("✅ tasdiqlangan" if status == "approved" else "📝 qoralama"),
        "",
        f"📅 Sana: {(inv.document_date.strftime('%d.%m.%Y') if inv.document_date else '—')}",
        f"🏢 Kontragent: {inv.supplier or 'tanlanmagan'}",
        f"    ИНН {inv.supplier_inn or '—'}",
        f"📄 {inv.contract or 'Shartnoma tanlanmagan'}",
        f"✍️ Qog‘ozda: {inv.source_supplier or inv.supplier or '—'}",
        f"📦 Kimga: {inv.recipient or '—'}",
        "",
    ]
    for n, item in enumerate(inv.items, 1):
        lines.append(
            f"{n}. {item.name or 'Nomi aniqlanmagan'} — {number(item.quantity)} {item.unit} × {number(item.price)} = {number(item.amount)}"
        )
    arithmetic_ok = (
        bool(inv.items)
        and inv.total is not None
        and all(
            (
                i.quantity is not None
                and i.price is not None
                and (i.amount is not None)
                and (
                    abs((i.quantity * i.price).quantize(Decimal(".01")) - i.amount)
                    <= Decimal(".01")
                )
                for i in inv.items
            )
        )
    )
    arithmetic_ok = arithmetic_ok and abs(
        sum((i.amount for i in inv.items), Decimal(0)) - inv.total
    ) <= Decimal(".01")
    lines.extend(
        [
            "",
            f"💰 Jami: {number(inv.total)} {inv.currency}"
            + (" (qog‘oz bilan mos)" if arithmetic_ok else " (tekshirish kerak)"),
        ]
    )
    if inv.warnings:
        lines.extend(["", "⚠️ O‘qishdagi noaniqliklar: " + "; ".join(inv.warnings)])
    errors = problems(inv)
    if errors:
        lines.extend(["", "⚠️ To‘ldirish / tekshirish: " + "; ".join(errors)])
    return "\n".join(lines)


def chunks(text, size=1900):
    while text:
        cut = text.rfind("\n", 0, size + 1) if len(text) > size else len(text)
        if cut <= 0:
            cut = size
        yield text[:cut]
        text = text[cut:].lstrip("\n")
