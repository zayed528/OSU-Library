"""Seed the in-memory store from data/seedData.json."""
import json
import os
from typing import Any

from .schemas import Book
from .store import add_book


def seed(seed_path: str | None = None) -> None:
    """Load JSON seed data and populate the store."""
    if seed_path is None:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        seed_path = os.path.join(base, "seedData.json")

    with open(seed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        # Expecting objects compatible with Book dataclass
        try:
            book = Book(**item)  # type: ignore[arg-type]
            add_book(book)
        except TypeError:
            # Skip invalid entries
            continue


if __name__ == "__main__":
    seed()
