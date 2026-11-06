from datetime import UTC, datetime

from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import DeclarativeBase

BigIntPrimaryKey = BigInteger().with_variant(Integer(), "sqlite")


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)
