from aiogram.types import InlineKeyboardButton as Button
from aiogram.types import InlineKeyboardMarkup


def actions(doc_id, approved=False):
    rows = [
        [Button(text="🏢 Kontragent tanlash", callback_data=f"inv:parties:{doc_id}")],
        [Button(text="✏️ Tahrirlash", callback_data=f"inv:edit:{doc_id}")],
    ]
    rows.append(
        [
            Button(
                text="📥 CSV olish" if approved else "✅ Tasdiqlash",
                callback_data=f"inv:{('csv' if approved else 'approve')}:{doc_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def party_buttons(doc_id, parties, page=0, has_next=False, query=""):
    rows = [
        [Button(text=p["name"][:100], callback_data=f"inv:choose:{doc_id}:{p['id']}")]
        for p in parties
    ]
    nav = []
    if page > 0:
        nav.append(Button(text="⬅️ Oldingi", callback_data=f"inv:page:{doc_id}:{page - 1}"))
    if has_next:
        nav.append(Button(text="Keyingi ➡️", callback_data=f"inv:page:{doc_id}:{page + 1}"))
    if nav:
        rows.append(nav)
    rows += [
        [
            Button(text="🔎 Qidirish", callback_data=f"inv:search:{doc_id}"),
            Button(text="➕ Yangi", callback_data=f"inv:new:{doc_id}"),
        ],
        [Button(text="⬅️ Orqaga", callback_data=f"inv:back:{doc_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
