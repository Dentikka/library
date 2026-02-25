#!/usr/bin/env python3
"""
Migration script: SQLite -> PostgreSQL
Перенос данных из SQLite в PostgreSQL

Usage:
    1. Убедитесь что PostgreSQL запущен
    2. Установите DATABASE_URL в .env (PostgreSQL)
    3. Запустите: python scripts/migrate_to_postgres.py
"""

import asyncio
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select

# Models
from app.models import Base, Author, Library, Book, Copy, StaffUser


# SQLite source (old)
SQLITE_URL = "sqlite+aiosqlite:///./library.db"

# PostgreSQL target (new) - from env or default
PG_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/library")


async def migrate():
    """Main migration function."""
    print("=" * 60)
    print("Library Database Migration: SQLite → PostgreSQL")
    print("=" * 60)
    
    # Create engines
    sqlite_engine = create_async_engine(SQLITE_URL, echo=False)
    pg_engine = create_async_engine(PG_URL, echo=False)
    
    try:
        # Test connections
        print("\n1. Testing connections...")
        async with sqlite_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("   ✅ SQLite connected")
        
        async with pg_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("   ✅ PostgreSQL connected")
        
        # Create tables in PostgreSQL
        print("\n2. Creating tables in PostgreSQL...")
        async with pg_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("   ✅ Tables created")
        
        # Create sessions
        SQLiteSession = sessionmaker(sqlite_engine, class_=AsyncSession, expire_on_commit=False)
        PGSession = sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
        
        async with SQLiteSession() as src, PGSession() as dst:
            # Migrate Authors
            print("\n3. Migrating Authors...")
            result = await src.execute(select(Author))
            authors = result.scalars().all()
            for author in authors:
                new_author = Author(
                    id=author.id,
                    name=author.name,
                    bio=author.bio,
                    created_at=author.created_at
                )
                dst.add(new_author)
            await dst.commit()
            print(f"   ✅ Migrated {len(authors)} authors")
            
            # Migrate Libraries
            print("\n4. Migrating Libraries...")
            result = await src.execute(select(Library))
            libraries = result.scalars().all()
            for lib in libraries:
                new_lib = Library(
                    id=lib.id,
                    name=lib.name,
                    address=lib.address,
                    phone=lib.phone,
                    email=lib.email,
                    created_at=lib.created_at
                )
                dst.add(new_lib)
            await dst.commit()
            print(f"   ✅ Migrated {len(libraries)} libraries")
            
            # Migrate Books
            print("\n5. Migrating Books...")
            result = await src.execute(select(Book))
            books = result.scalars().all()
            for book in books:
                new_book = Book(
                    id=book.id,
                    title=book.title,
                    isbn=book.isbn,
                    description=book.description,
                    year_published=book.year_published,
                    cover_image=book.cover_image,
                    author_id=book.author_id,
                    created_at=book.created_at
                )
                dst.add(new_book)
            await dst.commit()
            print(f"   ✅ Migrated {len(books)} books")
            
            # Migrate Copies
            print("\n6. Migrating Copies...")
            result = await src.execute(select(Copy))
            copies = result.scalars().all()
            for copy in copies:
                new_copy = Copy(
                    id=copy.id,
                    book_id=copy.book_id,
                    library_id=copy.library_id,
                    inventory_number=copy.inventory_number,
                    status=copy.status,
                    condition=copy.condition,
                    notes=copy.notes,
                    created_at=copy.created_at
                )
                dst.add(new_copy)
            await dst.commit()
            print(f"   ✅ Migrated {len(copies)} copies")
            
            # Migrate Staff Users
            print("\n7. Migrating Staff Users...")
            result = await src.execute(select(StaffUser))
            users = result.scalars().all()
            for user in users:
                new_user = StaffUser(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    full_name=user.full_name,
                    hashed_password=user.hashed_password,
                    is_active=user.is_active,
                    is_admin=user.is_admin,
                    created_at=user.created_at
                )
                dst.add(new_user)
            await dst.commit()
            print(f"   ✅ Migrated {len(users)} staff users")
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print(f"\nData migrated from:")
        print(f"  Source: {SQLITE_URL}")
        print(f"  Target: {PG_URL}")
        print("\nNext steps:")
        print("  1. Update .env with DATABASE_URL for PostgreSQL")
        print("  2. Restart the application")
        print("  3. Verify data integrity")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        await sqlite_engine.dispose()
        await pg_engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
