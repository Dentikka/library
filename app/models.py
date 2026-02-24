from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Author(Base):
    __tablename__ = "authors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    books = relationship("Book", back_populates="author", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.name}')>"


class Library(Base):
    __tablename__ = "libraries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    work_hours = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    copies = relationship("Copy", back_populates="library")
    staff = relationship("StaffUser", back_populates="library")
    
    def __repr__(self):
        return f"<Library(id={self.id}, name='{self.name}')>"


class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("authors.id", ondelete="SET NULL"), nullable=True)
    isbn = Column(String(13), unique=True, nullable=True, index=True)
    year = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Full-text search vector (will be populated by trigger or manually)
    search_vector = Column(Text, nullable=True)
    
    # Relationships
    author = relationship("Author", back_populates="books")
    copies = relationship("Copy", back_populates="book", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title[:30]}...')>"


class Copy(Base):
    __tablename__ = "copies"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    library_id = Column(Integer, ForeignKey("libraries.id", ondelete="CASCADE"), nullable=False)
    inventory_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), default="available", nullable=False)  # available, loaned, reserved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    book = relationship("Book", back_populates="copies")
    library = relationship("Library", back_populates="copies")
    
    def __repr__(self):
        return f"<Copy(id={self.id}, inv='{self.inventory_number}', status='{self.status}')>"


class StaffUser(Base):
    __tablename__ = "staff_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    library_id = Column(Integer, ForeignKey("libraries.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    library = relationship("Library", back_populates="staff")
    
    def __repr__(self):
        return f"<StaffUser(id={self.id}, username='{self.username}')>"


# Create index for full-text search
Index('ix_books_search_vector', Book.search_vector, postgresql_using='gin')
