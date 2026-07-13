"""v30.1 - transaction boundary helper."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


class TransactionManager:
    def __init__(self, database):
        self.database = database

    @contextmanager
    def transaction(self) -> Iterator:
        with self.database.session() as session:
            yield session
