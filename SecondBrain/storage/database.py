"""v30.1 - SQLAlchemy database engine factory.

Hard dependency on SQLAlchemy is isolated here. Modules can import repository
interfaces without requiring a live database.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from secondbrain.storage.database_config import DatabaseConfig


class DatabaseUnavailable(RuntimeError):
    pass


class Database:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine = None
        self._sessionmaker = None

    def engine(self):
        if self._engine is None:
            try:
                from sqlalchemy import create_engine, text
            except Exception as exc:
                raise DatabaseUnavailable("SQLAlchemy is not installed") from exc

            self._engine = create_engine(
                self.config.url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,
                future=True,
            )
            with self._engine.connect() as connection:
                connection.execute(
                    text(f"SET statement_timeout = {int(self.config.statement_timeout_ms)}")
                )
        return self._engine

    def sessionmaker(self):
        if self._sessionmaker is None:
            try:
                from sqlalchemy.orm import sessionmaker
            except Exception as exc:
                raise DatabaseUnavailable("SQLAlchemy is not installed") from exc
            self._sessionmaker = sessionmaker(bind=self.engine(), autoflush=False, autocommit=False, future=True)
        return self._sessionmaker

    @contextmanager
    def session(self) -> Iterator:
        factory = self.sessionmaker()
        session = factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
