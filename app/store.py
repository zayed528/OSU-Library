from typing import List
from .schemas import Book

# Simple in-memory store for Book objects
STORE: List[Book] = []


def add_book(book: Book) -> None:
    """Add a Book to the in-memory store."""
    STORE.append(book)


def list_books() -> List[Book]:
    """Return all books in the store."""
    return STORE
