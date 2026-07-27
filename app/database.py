"""PostgreSQL connection helpers for the telemetry platform."""

from contextlib import contextmanager
from collections.abc import Iterator

import psycopg2
from psycopg2.extensions import connection

from app.config import DatabaseSettings, load_database_settings


def create_connection(
    settings: DatabaseSettings | None = None,
) -> connection:
    config = settings or load_database_settings()

    return psycopg2.connect(
        host=config.host,
        database=config.database,
        user=config.user,
        password=config.password,
        port=config.port,
    )


@contextmanager
def database_connection(
    settings: DatabaseSettings | None = None,
) -> Iterator[connection]:
    conn = create_connection(settings)

    try:
        yield conn
    finally:
        conn.close()