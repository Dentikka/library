# Library — Library Management System

Современный легковесный каталог для централизованной библиотечной системы.

## Описание

Веб-приложение для поиска книг по каталогу библиотек с:
- Публичным поиском без авторизации
- Информацией о наличии книг в филиалах
- Панелью управления для сотрудников

## Технический стек

- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL
- **Search:** PostgreSQL Full-Text Search
- **Auth:** JWT (access + refresh tokens)
- **Frontend:** HTMX + Tailwind CSS
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic

## Структура проекта

```
library/
├── app/
│   ├── __init__.py
│   ├── main.py              # Точка входа FastAPI
│   ├── config.py            # Настройки (env vars)
│   ├── database.py          # Подключение к БД
│   ├── models/              # SQLAlchemy модели
│   ├── routers/             # API endpoints
│   ├── schemas/             # Pydantic схемы
│   └── services/            # Бизнес-логика
├── alembic/                 # Миграции БД
├── templates/               # Jinja2 шаблоны
├── static/                  # CSS, JS, изображения
├── reports/                 # Отчеты по задачам
├── tests/                   # Тесты
├── requirements.txt
├── pyproject.toml
├── alembic.ini
├── docker-compose.yml
└── README.md
```

## Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка БД
# Создать .env файл с DATABASE_URL

# Применение миграций
alembic upgrade head

# Заполнение тестовыми данными
python scripts/seed.py

# Запуск сервера
uvicorn app.main:app --reload

# Документация API
open http://localhost:8000/docs
```

## Лицензия

MIT
