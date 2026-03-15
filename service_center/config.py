from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    host: str = os.getenv("DB_HOST", "127.0.0.1")
    port: int = int(os.getenv("DB_PORT", "3306"))
    user: str = os.getenv("DB_USER", "course_user")
    password: str = os.getenv("DB_PASSWORD", "1910")
    database: str = os.getenv("DB_NAME", "service_center_db")
