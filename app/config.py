from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database - обязательная переменная окружения
    database_url: str
    
    # JWT - обязательная переменная окружения (нет дефолта!)
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 20
    refresh_token_expire_days: int = 7
    
    # App
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_critical_settings():
    """Валидация обязательных секретов при старте приложения.
    
    Вызывает ValueError с понятным сообщением, если критические
    переменные окружения не заданы.
    """
    import os
    
    missing = []
    
    # Проверяем DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        missing.append("DATABASE_URL")
    
    # Проверяем SECRET_KEY
    secret = os.getenv("SECRET_KEY")
    if not secret:
        missing.append("SECRET_KEY")
    elif len(secret) < 32:
        raise ValueError(
            "SECURITY ERROR: SECRET_KEY должен быть не менее 32 символов "
            "для обеспечения безопасности JWT токенов. "
            "Сгенерируйте ключ: openssl rand -hex 32"
        )
    
    if missing:
        raise ValueError(
            f"SECURITY ERROR: Отсутствуют обязательные переменные окружения: {', '.join(missing)}. "
            f"Скопируйте .env.example в .env и настройте значения."
        )
    
    # Проверка на использование дефолтных/слабых значений в production
    if secret in ("your-secret-key", "secret", "test", "123456"):
        raise ValueError(
            "SECURITY ERROR: SECRET_KEY использует слабое/тестовое значение. "
            "Сгенерируйте надёжный ключ: openssl rand -hex 32"
        )
