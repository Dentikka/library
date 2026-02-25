from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routers import auth, libraries, books, search, authors
from app.config import validate_critical_settings

# Валидация критических настроек при импорте модуля
# Вызывает ошибку с понятным сообщением если SECRET_KEY или DATABASE_URL не заданы
validate_critical_settings()


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
    return {"status": "ok"}
