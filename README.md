# Arena Go

[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-green)](https://fastapi.tiangolo.com/)
[![Aiogram](https://img.shields.io/badge/Aiogram-Telegram%20Bot-2AABEE)](https://docs.aiogram.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PostGIS-blue)](https://www.postgresql.org/)

Arena Go bu FastAPI + Telegram Bot asosidagi stadion topish va bron qilish tizimi. Loyiha foydalanuvchi lokatsiyasiga yaqin stadionlarni topadi, hudud bo'yicha stadionlarni ko'rsatadi, bron yaratadi, adminlarga bronlarni boshqarish imkonini beradi va superadminlar uchun role boshqaruvi ham mavjud.

## Project Overview

Ushbu loyiha ikki asosiy qismdan iborat:

- `FastAPI API`
  - user, stadium, booking va location endpoint'lari
  - admin va superadmin uchun ruxsat nazorati
  - PostGIS orqali geolocation qidiruv
- `Telegram Bot`
  - foydalanuvchini ro'yxatdan o'tkazish
  - lokatsiyaga yaqin stadionlarni topish
  - bron qilish va bronni bekor qilish
  - admin panel
  - superadmin panel

Tizim quyidagi real business flow'larni qo'llab-quvvatlaydi:

- foydalanuvchi region, district, local area va telefon orqali ro'yxatdan o'tadi
- foydalanuvchi lokatsiya yuborib eng yaqin stadionlarni ko'radi
- foydalanuvchi hududidagi stadionlardan bron qiladi
- foydalanuvchi o'z bronlarini ko'radi va bekor qiladi
- admin o'z stadionlariga tegishli bronlarni ko'radi va bekor qiladi
- superadmin admin tayinlaydi, adminni olib tashlaydi, stadion qo'shadi, yangi superadmin qo'shadi va superadminni olib tashlaydi

## Tech Stack

- Python 3.12
- FastAPI
- Aiogram
- SQLModel
- SQLAlchemy
- Alembic
- PostgreSQL
- PostGIS
- GeoAlchemy2
- Uvicorn
- HTTPX / AIOHTTP

## Main Features

### User Features

- Telegram orqali ro'yxatdan o'tish
- Region, district va local area tanlash
- Yaqin stadionlarni lokatsiya bo'yicha topish
- Hududidagi stadionlarni ko'rish
- Stadion detail sahifasi
- Sana va vaqt oralig'i bo'yicha bron qilish
- Mening bronlarim bo'limi
- Bronni bekor qilish

### Admin Features

- Faqat o'ziga biriktirilgan stadionlarni ko'radi
- Bugungi bronlarni ko'radi
- Stadion kesimida bronlarni ko'radi
- Bronni bekor qiladi
- Bekor qilinganda foydalanuvchiga Telegram notification boradi

### Superadmin Features

- Barcha stadionlarni ko'radi
- Stadion qo'shadi
- Stadionga admin tayinlaydi
- Stadion adminlarini boshqaradi
- Yangi superadmin qo'shadi
- Superadminlarni boshqaradi
- Superadminni olib tashlaydi

### Platform Features

- Role-based visibility
- Role-based backend authorization
- Global exception handling
- Markazlashgan logging
- Telegram orqali error reporting
- Public va internal xatolarni ajratish

## Roles

Tizimda 3 ta role mavjud:

- `user`
  - oddiy foydalanuvchi
  - stadion topadi va bron qiladi
- `admin`
  - o'z stadionlari bo'yicha bronlarni boshqaradi
- `superadmin`
  - tizimdagi barcha stadion va role boshqaruviga ega

Muhim:

- `admin`ga tegishli tugmalar faqat `admin` va `superadmin`ga ko'rinadi
- `superadmin`ga tegishli tugmalar faqat `superadmin`ga ko'rinadi
- backend darajasida ham ruxsatlar tekshiriladi, faqat UI yashirish bilan cheklanilmagan

## Project Structure

```text
fast-api-bot/
├── app/
│   ├── bot/
│   │   ├── handlers/
│   │   │   ├── admin/
│   │   │   └── user/
│   │   ├── keyboards/
│   │   ├── states/
│   │   └── dispatcher.py
│   ├── core/
│   │   ├── config.py
│   │   ├── error_handling.py
│   │   └── logger.py
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── scripts/
│   ├── services/
│   ├── database.py
│   ├── dev_start.py
│   └── main.py
├── logs/
├── migrations/
├── .env
├── .env.example
├── .env.seed
├── .env.seed.example
├── alembic.ini
├── requirements.txt
└── README.md
```

## Environment Variables

Loyiha `.env` orqali boshqariladi.

### Main Environment File

`.env.example` ichidagi kalitlar:

| Key | Description |
|---|---|
| `DATABASE_URL_SYNC` | Sync PostgreSQL connection string |
| `DATABASE_URL_ASYNC` | Async PostgreSQL connection string |
| `BOT_TOKEN` | Asosiy Telegram bot tokeni |
| `ERROR_BOT_TOKEN` | Error log yuboradigan Telegram bot tokeni |
| `ERROR_BOT_CHAT_ID` | Error log boradigan Telegram chat ID |
| `WEBHOOK_URL` | Webhook URL, agar webhook ishlatilsa |
| `WEBHOOK_PATH` | Webhook path |
| `BASE_URL` | Bot API so'rov yuboradigan FastAPI base URL |
| `LOG_LEVEL` | Logger level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FILE_PATH` | Log fayl manzili |
| `SQL_ECHO` | SQL query loglarni yoqish/o'chirish |

### Seed Environment File

`.env.seed.example` ichidagi:

- `SUPERADMINS`

Bu JSON array bo'lib, boshlang'ich superadmin'larni seed qilish uchun ishlatiladi.

## Example Environment

```env
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@localhost:5432/arena_go
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:postgres@localhost:5432/arena_go

BOT_TOKEN=123456:telegram-bot-token
ERROR_BOT_TOKEN=123456:error-bot-token
ERROR_BOT_CHAT_ID=-1001234567890

WEBHOOK_URL=
WEBHOOK_PATH=/webhook

BASE_URL=http://localhost:8000/api

LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log
SQL_ECHO=false
```

## Database Requirements

Loyiha PostgreSQL va PostGIS bilan ishlaydi. `location` maydonlari `geography(POINT, 4326)` tipidan foydalanadi.

PostGIS yoqilishi kerak:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/mirkamolhomidov/fast-api-bot.git
cd fast-api-bot
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
cp .env.seed.example .env.seed
```

Keyin `.env` va `.env.seed` ni o'zingizning ma'lumotlaringiz bilan to'ldiring.

### 5. Run Database Migrations

```bash
alembic upgrade head
```

Eslatma:

- API startup paytida `create_all()` ham ishlaydi
- production yoki boshqariladigan muhitda asosan Alembic migration ishlatish tavsiya qilinadi

### 6. Seed Initial Superadmin

Agar tizimda hali superadmin bo'lmasa:

```bash
python -m app.scripts.seed_superadmin
```

Yoki:

```bash
python app/scripts/seed_superadmin.py
```

## Running the Project

### Run FastAPI API

```bash
uvicorn app.main:app --reload
```

API:

- Root: `http://127.0.0.1:8000/`
- Swagger Docs: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

### Run Telegram Bot

```bash
python -m app.dev_start
```

Yoki:

```bash
python app/dev_start.py
```

## API Prefixes

Barcha asosiy endpoint'lar `/api` prefix bilan ishlaydi:

- `/api/locations`
- `/api/stadiums`
- `/api/bookings`
- `/api/users`

## Key API Endpoints

### Locations

- `GET /api/locations/regions`
- `GET /api/locations/districts`
- `GET /api/locations/local-areas`

### Stadiums

- `GET /api/stadiums/nearest`
- `GET /api/stadiums/location`
- `GET /api/stadiums/managed`
- `POST /api/stadiums/create`

### Bookings

- `GET /api/bookings/`
- `GET /api/bookings/my/{telegram_id}`
- `GET /api/bookings/admin/{telegram_id}`
- `POST /api/bookings/create-booking`
- `PATCH /api/bookings/update-booking/{booking_id}`
- `PATCH /api/bookings/cancel-booking/{booking_id}`
- `DELETE /api/bookings/delete-booking/{booking_id}`

### Users

- `POST /api/users/create`
- `POST /api/users/create/admin`
- `POST /api/users/create/superadmin`
- `GET /api/users/superadmins`
- `DELETE /api/users/superadmins/{user_id}`
- `GET /api/users/stadium-admins/{stadium_id}`
- `DELETE /api/users/stadium-admins/{stadium_admin_id}`
- `GET /api/users/{telegram_id}`

## Telegram Bot Flows

### User Flow

1. `/start`
2. Region tanlash
3. District tanlash
4. Local area tanlash
5. Telefon yuborish
6. Asosiy menyu
7. Stadion qidirish yoki hududdagi stadionlarni ko'rish
8. Bron qilish

### Admin Flow

1. `🛠 Admin panel`
2. `📅 Bugungi bronlar`
3. Stadion tanlash
4. Sana tanlash
5. Bronlarni ko'rish
6. Bronni bekor qilish

### Superadmin Flow

1. `🛠 Admin panel`
2. `🏟 Stadion qo'shish`
3. `👑 Superadmin qo'shish`
4. `🧾 Superadminlarni boshqarish`
5. `➕ Admin tayinlash`
6. `👥 Adminlarni boshqarish`

## Logging and Error Handling

Loyihada markazlashgan logging tizimi mavjud.

### Logging Sources

- FastAPI request lifecycle
- Service layer exceptions
- Bot runtime exceptions
- Validation warnings
- File log
- Telegram error bot

### User-facing Error Policy

- foydalanuvchiga ichki stack trace ko'rsatilmaydi
- `500` tipidagi xatolar sanitize qilinadi
- logda esa to'liq kontekst saqlanadi

### Logged Metadata

Logger quyidagilarni saqlaydi:

- vaqt
- level
- logger name
- file
- line
- function context
- status code
- extra context
- traceback

### Log Files

Default:

```text
logs/app.log
```

### Telegram Error Bot

Agar quyidagilar to'ldirilsa:

- `ERROR_BOT_TOKEN`
- `ERROR_BOT_CHAT_ID`

xatoliklar Telegram chat'ga yuboriladi.

## Notes About SQL_ECHO

- `SQL_ECHO=true`
  - barcha SQL query'lar logga chiqadi
  - debug uchun foydali
  - production uchun tavsiya qilinmaydi
- `SQL_ECHO=false`
  - oddiy va toza log
  - production uchun xavfsizroq

## Architecture Notes

Loyihada quyidagi yondashuv ishlatilgan:

- `routers` faqat request/response bilan ishlaydi
- `services` business logic'ni bajaradi
- `schemas` validation uchun ishlatiladi
- `models` database structure'ni beradi
- `core` config, logger va error handling'ni markazlashtiradi
- `bot/handlers` Telegram flow'larni boshqaradi

Bu yondashuv:

- readability'ni oshiradi
- dry tamoyiliga yaqinlashtiradi
- exception handling'ni markazlashtiradi
- role-based logic'ni ajratishga yordam beradi

## Development Notes

Debug paytda foydali komandalar:

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
uvicorn app.main:app --reload
python -m app.dev_start
```

## Current Status

Hozirgi holatda loyiha:

- FastAPI API bilan ishlaydi
- Telegram bot bilan ishlaydi
- bron qilish oqimi ishlaydi
- admin panel ishlaydi
- superadmin panel ishlaydi
- logging tizimi ishlaydi
- error sanitization ishlaydi
- role-based visibility va backend authorization ishlaydi

## Future Improvements

Quyidagilar keyingi bosqichlarda qo'shilishi mumkin:

- webhook deployment
- Docker support
- test suite
- CI/CD
- caching
- pagination
- audit trail
- notification templates

## License

Ushbu loyiha shaxsiy yoki ichki foydalanish uchun moslashtirilgan. Agar alohida license fayli qo'shilsa, shu bo'yicha foydalaniladi.
