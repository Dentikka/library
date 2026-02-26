# Библиотека

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

## Backup & Restore

### Создание бэкапа

```bash
# Установить переменные окружения (или в .env)
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/library_db"
export BACKUP_DIR="./backups"
export BACKUP_RETENTION_DAYS=7

# Запуск бэкапа
python scripts/backup.py
```

Бэкапы сохраняются в `BACKUP_DIR` с именем `library_YYYYMMDD_HHMMSS.sql.gz`.
Автоматически удаляются бэкапы старше `BACKUP_RETENTION_DAYS` дней.

### Настройка cron (автоматические бэкапы)

```bash
# Редактирование crontab
crontab -e

# Ежедневный бэкап в 2:00 ночи
0 2 * * * cd /path/to/library && /path/to/venv/bin/python scripts/backup.py >> /var/log/library-backup.log 2>&1
```

### Восстановление из бэкапа

```bash
# Распаковать бэкап
gunzip -c library_20250226_143000.sql.gz > restore.sql

# Восстановление в существующую базу
export PGPASSWORD="your_password"
psql -h localhost -U library_user -d library_db -f restore.sql

# Или восстановление в новую базу
psql -h localhost -U postgres -c "CREATE DATABASE library_db_new;"
psql -h localhost -U library_user -d library_db_new -f restore.sql
```

**Важно:** Перед восстановлением убедитесь, что:
1. PostgreSQL клиент установлен (`pg_dump`, `psql`)
2. База данных доступна и пуста (или её можно пересоздать)
3. Пользователь имеет права на создание таблиц

## Лицензия

MIT
