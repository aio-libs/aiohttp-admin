"""Database models used for examples."""

from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    books: Mapped[list["Book"]] = relationship()


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author_id: Mapped[int | None] = mapped_column(sa.ForeignKey(Author.id))

    # author: Mapped[Author] = relationship(back_populates="books")
