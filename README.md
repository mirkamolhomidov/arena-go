# FastAPI Stadium Management API

[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 🏟 Project Overview

**FastAPI Stadium Management API** — bu RESTful API loyihasi bo‘lib, stadionlar, hududlar (regions) va mahalliy hududlar (local areas) bilan ishlash imkonini beradi.  
Loyiha **PostgreSQL + PostGIS** bilan ishlaydi va **geospatial queries** (stadion joylashuvlari bo‘yicha) uchun optimizatsiya qilingan.

Ushbu loyiha yordamida:
- Stadionlar, hududlar va mahalliy hududlar bilan CRUD amallarini bajarish mumkin.
- Hududga yoki mahalliy hududga qarab stadionlarni filtr qilish.
- Geospatial ma’lumotlar bilan ishlash (location point).

---

## ⚡ Tech Stack

- **Python 3.12**  
- **FastAPI** — Web framework  
- **SQLAlchemy** — ORM  
- **Alembic** — Database migrations  
- **PostgreSQL + PostGIS** — Database va geospatial extensions  
- **Pydantic** — Data validation  
- **Uvicorn** — ASGI server  

---

## 🛠 Features

- CRUD operations:
  - Stadiums
  - Regions
  - Local Areas
- Geospatial support using PostGIS (`POINT` for stadium location)
- Alembic migrations for database schema versioning
- Swagger UI documentation (`/docs`)
- Clean project structure for easy extension

---

## 🚀 Installation

### Clone repository

```bash
git clone https://github.com/mirkamolhomidov/fast-api-bot.git
cd fast-api-bot
