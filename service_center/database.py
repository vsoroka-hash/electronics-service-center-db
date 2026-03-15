from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable

import mysql.connector
from mysql.connector.connection import MySQLConnection
from mysql.connector.pooling import MySQLConnectionPool

from .config import Config


class Database:
    _pools: dict[tuple[str, int, str, str], MySQLConnectionPool] = {}

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        pool_key = (self.config.host, self.config.port, self.config.user, self.config.database)
        if pool_key not in self._pools:
            pool_name = f"service_center_pool_{len(self._pools) + 1}"
            self._pools[pool_key] = MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=5,
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
            )
        self._pool = self._pools[pool_key]

    def connect(self) -> MySQLConnection:
        return self._pool.get_connection()

    @contextmanager
    def cursor(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                yield connection, cursor

    def fetch_all(self, query: str, params: tuple | None = None) -> list[tuple]:
        with self.cursor() as (_, cursor):
            cursor.execute(query, params or ())
            return cursor.fetchall()

    def execute(self, query: str, params: tuple | None = None) -> None:
        with self.cursor() as (connection, cursor):
            cursor.execute(query, params or ())
            connection.commit()

    def execute_many(self, query: str, rows: Iterable[tuple]) -> None:
        with self.cursor() as (connection, cursor):
            cursor.executemany(query, list(rows))
            connection.commit()

    def call_procedure(self, name: str, args: list) -> None:
        with self.cursor() as (connection, cursor):
            cursor.callproc(name, args)
            connection.commit()
