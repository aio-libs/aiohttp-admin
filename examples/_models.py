"""Database models used for examples."""

from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Currency(Enum):
    EUR = "EUR"
    GBP = "GBP"
    USD = "USD"


class Base(DeclarativeBase):
    """Base model."""


class Simple(Base):
    __tablename__ = "simple"

    id: Mapped[int] = mapped_column(primary_key=True)
    num: Mapped[int]
    optional_num: Mapped[float | None]
    value: Mapped[str]


class SimpleParent(Base):
    __tablename__ = "parent"

    id: Mapped[int] = mapped_column(sa.ForeignKey(Simple.id, ondelete="CASCADE"),
                                    primary_key=True)
    date: Mapped[datetime]
    currency: Mapped[Currency] = mapped_column(default="USD")
