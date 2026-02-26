from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routers import auth, libraries, books, search, authors
from app.config import validate_critical_settings
from app.logging_config import setup_logging, get_logger
from app.middleware import RequestLoggingMiddleware, ErrorLoggingMiddleware

# Валидация критических настроек при импорте модуля
# Вызывает ошибку с понятным сообщением если SECRET_KEY или DATABASE_URL не заданы
validate_critical_settings()

# Setup structured logging (use JSON in production, console in development)
import os
log_format = os.getenv("LOG_FORMAT", "console")
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE")  # Optional file logging
setup_logging(level=log_level, format_type=log_format, log_file=log_file)

logger = get_logger(__name__)
logger.info("Library Management System starting up")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Library Management System",
    description="Каталог книг для ЦБС Вологды",
    version="0.1.0",
    lifespan=lifespan,
)

# Add logging middleware
app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Include API routers
app.include_router(auth.router)
app.include_router(libraries.router)
app.include_router(books.router)
app.include_router(search.router)
app.include_router(authors.router)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main page with search."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = ""):
    """Search results page."""
    return templates.TemplateResponse("search.html", {"request": request, "query": q})


@app.get("/books/{book_id}", response_class=HTMLResponse)
async def book_detail_page(request: Request, book_id: int):
    """Book detail page."""
    return templates.TemplateResponse("book_detail.html", {"request": request, "book_id": book_id})


@app.get("/libraries", response_class=HTMLResponse)
async def libraries_page(request: Request):
    """Libraries list page."""
    return templates.TemplateResponse("libraries.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """About page."""
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/staff/login", response_class=HTMLResponse)
async def staff_login_page(request: Request):
    """Staff login page."""
    return templates.TemplateResponse("staff/login.html", {"request": request})


@app.get("/staff/dashboard", response_class=HTMLResponse)
async def staff_dashboard_page(request: Request):
    """Staff dashboard page."""
    return templates.TemplateResponse("staff/dashboard.html", {"request": request})


@app.get("/health")
async def health():
    """Health check endpoint for monitoring.
    
    Returns:
        - status: 'ok' or 'error'
        - version: API version
        - timestamp: Current UTC timestamp
    """
    from datetime import datetime, timezone
    return {
        "status": "ok",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
