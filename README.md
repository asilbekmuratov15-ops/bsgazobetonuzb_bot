# Nakladnoy → Telegram → CSV

Python + aiogram, PostgreSQL, Groq Vision. Interfeys o‘zbekcha.

Railway uchun ko‘rsatma: [RAILWAY.md](RAILWAY.md). Konteyner `Dockerfile` orqali quriladi.

Rasm natijasi o‘qishga qulay Telegram xabarida chiqadi. Pastdagi tugmalar orqali kontragentni tanlash, nom/INN bo‘yicha qidirish va yangisini `INN; 1C dagi nomi; Shartnoma` formatida saqlash mumkin. Ro‘yxat foydalanuvchi bo‘yicha PostgreSQL’da saqlanadi va har sahifada 5 ta nom ko‘rsatiladi. `/bekor` kiritishni bekor qiladi. Tanlashda INN va shartnoma birga to‘ldiriladi, tasdiqlangan hujjat qayta qoralamaga aylanadi. Qog‘ozdagi dastlabki yetkazib beruvchi alohida saqlanadi. `Tasdiqlash` va `CSV olish` tugmalari mavjud; odatdagi matnli buyruqlar ham ishlaydi.

## Ishga tushirish

1. `.env` faylida `TELEGRAM_BOT_TOKEN`, `GROQ_API_KEY`, `ALLOWED_USER_IDS` ni kiriting. Bot tokeni BotFather orqali olinadi. ID — ruxsat berilgan shaxslarning Telegram raqamli user ID qiymatlari, telefon raqami emas. Kalitlarni Git yoki chatga joylamang.
2. PowerShell: `./start-db.ps1`, keyin `./start.ps1`.
3. Telegramda `/start`, keyin nakladnoy rasmini yuboring.
4. `/set` va `/row` yordamida qiymatlarni tekshiring/tuzating. Nomenklatura kodi va kontragent nomi 1C ma’lumotnomasiga aynan mos bo‘lishi kerak.
5. `/approve ID`, so‘ng `/csv ID`; kunlik to‘plam uchun `/batch 2026-11-03`.

Bot ishlashi uchun kompyuter va ikkala jarayon ishlab turishi kerak. Windows qayta yoqilganda skriptlarni qayta ishga tushiring. Ma’lumotlar `work/pgdata` ichida saqlanadi. Zaxiralash uchun PostgreSQL `pg_dump` vositasidan foydalaning. Hozir avtomatik ishga tushirish yoki hosting sozlanmagan.

## 1C bilan moslashtirish

Skrinshotlar import formati emas, “Поступление материалов” ro‘yxatini ko‘rsatadi. Shu sabab universal CSV ni barcha 1C konfiguratsiyalari bevosita qabul qiladi deb bo‘lmaydi. Sizning konfiguratsiyangizdagi CSV import ishlovi yoki tashqi `.epf` yuklagich kerak. Avval test bazasida sinang.

`csv_profile.json` ustun nomlari va tartibi, kodlash, ajratgich va kasr belgisini boshqaradi. Standart: UTF-8 BOM, nuqtali vergul, kasr uchun vergul. 1C yuklagichidagi kutilgan ustunlarga moslang. Har tovar uchun bitta qator; hujjat ID bo‘yicha guruhlang. `Сумма документа` har qatorda takrorlanadi — uni yig‘mang. Hujjat raqami yo‘q bo‘lsa bo‘sh qoladi; 1C ichki raqamini yuklagich yaratsin. Bot 1C ga hujjat yozmaydi yoki проводка qilmaydi.

`sample.csv` — qo‘lda tuzilgan namuna (rasmdan Groq orqali o‘qilgan natija emas). 2 × 250000 + 4 × 35000 + 2 × 40000 = 720000.

## Tekshiruv va cheklovlar

Noaniq matn va raqamlarni AI xato o‘qishi mumkin. Ogohlantirishlar preview ichida ko‘rsatiladi. `/approve` — foydalanuvchining ko‘z bilan tekshirganini bildiradi. Miqdor × narx va jami mos bo‘lmasa CSV bloklanadi. Shartnoma, ombor, sana, kontragent va jami majburiy. INN va kodlarni AI o‘ylab topmasligi so‘ralgan; ularni zarur bo‘lsa qo‘lda kiriting. Standart QQS — `Без НДС`; kerak bo‘lsa `/set ID vat ...` orqali almashtiring. QQS hisoblash, valyuta konvertatsiyasi va katalogga avtomatik moslashtirish yo‘q.

Bir xil rasm baytlari qayta yuborilsa oldingi hujjat ochiladi. Qayta suratga olingan yoki siqilgan boshqa nusxa alohida hujjat bo‘lishi mumkin. Har rasm bitta hujjat, ko‘p sahifali va PDF qabul qilinmaydi. `/batch` qayta eksport qilishi mumkin, importda ID bo‘yicha dublikatdan himoya kerak.

Rasmlar Groq API ga uzatiladi, mahalliy bazada tanilgan ma’lumotlar saqlanadi. Bot faqat ruxsat berilgan ID va shaxsiy chatda ishlaydi. API kalitlari va rasm mazmuni logga chiqarilmaydi.

## Boshqa kompyuterga o‘rnatish

Python 3.12+, PostgreSQL 17+ o‘rnating. Virtual muhit yarating va `pip install -r requirements.txt` bajaring. PostgreSQLda alohida foydalanuvchi va bo‘sh baza yarating, `.env.example` ni `.env` ga ko‘chirib DATABASE_URL ni sozlang. `python bot.py` jadvallarni yaratadi. Mahalliy start skriptlari ushbu workspace ichidagi portable o‘rnatishga mo‘ljallangan.

Test: `python -m unittest -v`. API kalitlarisiz arifmetika va CSV tekshiriladi. Haqiqiy Groq/Telegram sinovi uchun kalitlar kerak.

Mahalliy tekshiruv natijasi: 3 test o‘tdi; PostgreSQL insert/dublikat/foydalanuvchi ajratilishi/tasdiqlash/tahrirdan keyin draft holatiga qaytish sinovlari o‘tdi; bot importi yuklandi; `pip check` xatosiz. Groq orqali berilgan rasm jonli tekshirildi: 3 qator, jami 720000. Telegram getMe va Groq models HTTP 200 qaytardi. 1C importi hali tekshirilmagan. O‘rnatilgan aniq paket versiyalari `requirements.txt` ichida.

Groq Vision: https://console.groq.com/docs/vision

Groq modeli `GROQ_MODEL` orqali sozlanadi; hozir `qwen/qwen3.8-27b`. Javob JSON mode orqali olinib Pydantic bilan tekshiriladi. Admin kirishi `ALLOWED_USER_IDS` bilan boshqariladi.

