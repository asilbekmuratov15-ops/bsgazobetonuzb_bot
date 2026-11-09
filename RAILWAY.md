# Railway ga joylash

Bot Dockerfile orqali Python 3.12 konteynerida ishga tushadi. Telegram long polling ishlatiladi; HTTP domen va PORT kerak emas.

1. Railway → New Project → Deploy from GitHub repo → `asilbekmuratov15-ops/bsgazobetonuzb_bot`.
2. Shu loyihaga PostgreSQL service qo‘shing. Uning nomini `Postgres` qoldiring yoki quyidagi reference ichida haqiqiy nomini yozing.
3. Bot service → Variables ichida quyidagilarni kiriting:

| Variable | Qiymat |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | BotFather tokeningiz |
| `GROQ_API_KEY` | Groq API kalitingiz |
| `GROQ_MODEL` | `qwen/qwen3.8-27b` |
| `ALLOWED_USER_IDS` | `8015824131` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `DEFAULT_WAREHOUSE` | 1C dagi ombor/bo‘linma nomi, ixtiyoriy |
| `DEFAULT_CONTRACT` | Shartnoma, ixtiyoriy |
| `DEFAULT_RESPONSIBLE` | Mas’ul, ixtiyoriy |

Token va API kalitini faqat Railway Variables ichiga kiriting. `.env` GitHub va Docker image ichiga kiritilmaydi. DATABASE_URL mahalliy `127.0.0.1` manzili emas, Railway PostgreSQL reference qiymati bo‘lsin.

4. Settings: Root Directory — repo ildizi; builder — Dockerfile. Start command Dockerfile ichida `python bot.py`. Replicas — **1**, Serverless/sleep — **o‘chiq**, Restart policy — **On Failure**. Healthcheck Path ni bo‘sh qoldiring: bot HTTP server emas. O‘tishdagi ikki polling nusxasi to‘qnashmasligi uchun eski deployni tugatish vaqtini minimal qiling.
5. Mahalliy kompyuterdagi botni to‘xtating, keyin Railway deployni boshlang. Bitta Telegram tokeni bilan bir vaqtning o‘zida faqat bitta polling bot ishlasin. `Conflict: terminated by other getUpdates request` xatosi boshqa nusxa ham ishlayotganini bildiradi.
6. Logs ichida `Bot ishga tushdi: @...` ni tekshiring. Telegramda `/start`, rasm, tekshirish/tuzatish, `/approve ID`, `/csv ID` ketma-ketligini sinang.

Baza jadvallari bot boshlanganda avtomatik yaratiladi. PostgreSQL volume va backup sozlamalarini Railway service ichida boshqaring. Mahalliy bazadagi oldingi hujjatlar bu deploy bilan ko‘chmaydi; ularni ko‘chirish uchun alohida `pg_dump`/restore kerak.

Bot service uchun alohida volume kerak emas: hujjatlar PostgreSQLda, CSV esa xotirada yaratiladi. Build vaqtida hech qanday kalit kerak emas. Ushbu repozitoriy tayyorlash jarayonida Railway hisobiga deploy qilinmagan.

Manbalar: [Dockerfile build](https://docs.railway.com/builds/dockerfiles), [PostgreSQL](https://docs.railway.com/databases/postgresql), [Variables references](https://docs.railway.com/variables/reference), [Restart policy](https://docs.railway.com/deployments/restart-policy).
