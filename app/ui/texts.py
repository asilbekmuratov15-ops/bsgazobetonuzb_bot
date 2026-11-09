HELP = """Nakladnoy rasmini yuboring (JPEG/PNG, 10 MB gacha).
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
Har rasm alohida hujjat. Ko‘p sahifali hujjatni bitta rasm qilib yuboring."""
