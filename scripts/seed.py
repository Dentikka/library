"""
Seed script to populate database with test data.
Run: python scripts/seed.py
"""
import asyncio
import sys
sys.path.append('.')

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal, engine
from app.models import Author, Library, Book, Copy, StaffUser
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_libraries(session: AsyncSession):
    """Create test libraries."""
    libraries = [
        Library(
            name="Центральная библиотека им. В.И. Белова",
            address="г. Вологда, ул. Пушкинская, 2",
            phone="(8172) 72-33-45",
            work_hours="Пн-Пт: 10:00-19:00, Сб: 10:00-18:00"
        ),
        Library(
            name="Библиотека на Панкратова",
            address="г. Вологда, ул. Панкратова, 35",
            phone="(8172) 52-41-83",
            work_hours="Пн-Пт: 11:00-19:00, Сб: 11:00-17:00"
        ),
        Library(
            name="Библиотека на Добролюбова",
            address="г. Вологда, ул. Добролюбова, 23",
            phone="(8172) 72-48-92",
            work_hours="Пн-Пт: 11:00-19:00, Сб: 11:00-17:00"
        ),
    ]
    
    for lib in libraries:
        session.add(lib)
    
    await session.commit()
    print(f"✓ Created {len(libraries)} libraries")
    return libraries


async def seed_authors(session: AsyncSession):
    """Create test authors."""
    authors_data = [
        ("Лев Толстой", "Русский писатель, автор романов 'Война и мир' и 'Анна Каренина'"),
        ("Федор Достоевский", "Русский писатель, автор 'Преступления и наказания'"),
        ("Александр Пушкин", "Великий русский поэт и писатель"),
        ("Антон Чехов", "Русский писатель и драматург"),
        ("Михаил Булгаков", "Автор 'Мастера и Маргариты'"),
        ("Николай Гоголь", "Русский писатель, автор 'Мертвых душ'"),
        ("Иван Тургенев", "Русский писатель, автор 'Отцов и детей'"),
        ("Виктор Гюго", "Французский писатель, автор 'Отверженных'"),
        ("Джордж Оруэлл", "Английский писатель, автор '1984'"),
        ("Эрнест Хемингуэй", "Американский писатель, лауреат Нобелевской премии"),
    ]
    
    authors = []
    for name, bio in authors_data:
        author = Author(name=name, bio=bio)
        session.add(author)
        authors.append(author)
    
    await session.commit()
    print(f"✓ Created {len(authors)} authors")
    return authors


async def seed_books(session: AsyncSession, authors: list):
    """Create test books."""
    books_data = [
        ("Война и мир", 0, "978-5-17-087577-2", 1869, "Эпопея о войне 1812 года"),
        ("Анна Каренина", 0, "978-5-17-087578-9", 1877, "Роман о любви и долге"),
        ("Преступление и наказание", 1, "978-5-17-087579-6", 1866, "Философский роман"),
        ("Идиот", 1, "978-5-17-087580-2", 1869, "Роман о 'идеальном человеке'"),
        ("Евгений Онегин", 2, "978-5-17-087581-9", 1833, "Роман в стихах"),
        ("Капитанская дочка", 2, "978-5-17-087582-6", 1836, "Исторический роман"),
        ("Вишневый сад", 3, "978-5-17-087583-3", 1904, "Пьеса в 4 действиях"),
        ("Чайка", 3, "978-5-17-087584-0", 1896, "Комедия в 4 действиях"),
        ("Мастер и Маргарита", 4, "978-5-17-087585-7", 1967, "Мистический роман"),
        ("Собачье сердце", 4, "978-5-17-087586-4", 1925, "Повесть-фельетон"),
        ("Мертвые души", 5, "978-5-17-087587-1", 1842, "Поэма в прозе"),
        ("Ревизор", 5, "978-5-17-087588-8", 1836, "Комедия в 5 действиях"),
        ("Отцы и дети", 6, "978-5-17-087589-5", 1862, "Роман о поколениях"),
        ("Ася", 6, "978-5-17-087590-1", 1858, "Повесть о любви"),
        ("Отверженные", 7, "978-5-17-087591-8", 1862, "Роман о справедливости"),
        ("Собор Парижской Богоматери", 7, "978-5-17-087592-5", 1831, "Исторический роман"),
        ("1984", 8, "978-5-17-087593-2", 1949, "Антиутопический роман"),
        ("Скотный двор", 8, "978-5-17-087594-9", 1945, "Сатирическая повесть"),
        ("Старик и море", 9, "978-5-17-087595-6", 1952, "Повесть о мужестве"),
        ("Прощай, оружие!", 9, "978-5-17-087596-3", 1929, "Роман о войне и любви"),
    ]
    
    books = []
    for title, author_idx, isbn, year, description in books_data:
        book = Book(
            title=title,
            author_id=authors[author_idx].id,
            isbn=isbn,
            year=year,
            description=description,
            search_vector=f"{title} {authors[author_idx].name}"  # Simple search vector
        )
        session.add(book)
        books.append(book)
    
    await session.commit()
    print(f"✓ Created {len(books)} books")
    return books


async def seed_copies(session: AsyncSession, books: list, libraries: list):
    """Create book copies in libraries."""
    copies = []
    copy_num = 1000
    
    for book in books:
        # Create 1-3 copies per book in random libraries
        num_copies = (book.id % 3) + 1
        for i in range(num_copies):
            library_idx = (book.id + i) % len(libraries)
            copy = Copy(
                book_id=book.id,
                library_id=libraries[library_idx].id,
                inventory_number=f"INV-{copy_num}",
                status="available" if i % 3 != 0 else "loaned"
            )
            session.add(copy)
            copies.append(copy)
            copy_num += 1
    
    await session.commit()
    print(f"✓ Created {len(copies)} book copies")
    return copies


async def seed_staff(session: AsyncSession, libraries: list):
    """Create staff users."""
    staff_data = [
        ("admin", "admin123", "Администратор", None, True, True),
        ("librarian1", "lib123", "Иванова Мария", libraries[0].id, True, False),
        ("librarian2", "lib123", "Петрова Анна", libraries[1].id, True, False),
    ]
    
    for username, password, full_name, lib_id, is_active, is_admin in staff_data:
        staff = StaffUser(
            username=username,
            hashed_password=pwd_context.hash(password),
            full_name=full_name,
            library_id=lib_id,
            is_active=is_active,
            is_admin=is_admin
        )
        session.add(staff)
    
    await session.commit()
    print(f"✓ Created {len(staff_data)} staff users")
    print("  - admin / admin123 (admin)")
    print("  - librarian1 / lib123 (staff)")
    print("  - librarian2 / lib123 (staff)")


async def seed_all():
    """Run all seed operations."""
    async with AsyncSessionLocal() as session:
        try:
            print("Seeding database...\n")
            
            libraries = await seed_libraries(session)
            authors = await seed_authors(session)
            books = await seed_books(session, authors)
            copies = await seed_copies(session, books, libraries)
            await seed_staff(session, libraries)
            
            print(f"\n✅ Database seeded successfully!")
            print(f"   - {len(libraries)} libraries")
            print(f"   - {len(authors)} authors")
            print(f"   - {len(books)} books")
            print(f"   - {len(copies)} copies")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_all())
