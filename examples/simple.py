"""Minimal example with simple database models.

When running this file, admin will be accessible at /admin.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path

import sqlalchemy as sa
from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

import aiohttp_admin
from aiohttp_admin.backends.sqlalchemy import SAResource
from aiohttp_admin.types import comp

# Example DB models


class Currency(Enum):
    EUR = 1
    GBP = 2
    USD = 3


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


async def check_credentials(username: str, password: str) -> bool:
    return username == "admin" and password == "admin"


async def serve_js(request):
    js = Path(__file__).with_name("custom-clone.js").read_text()
    return web.Response(text=js, content_type="text/javascript")


async def create_app() -> web.Application:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session = async_sessionmaker(engine, expire_on_commit=False)

    # Create some sample data
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session.begin() as sess:
        sess.add(Simple(num=5, value="first"))
        p = Simple(num=82, optional_num=12, value="with child")
        sess.add(p)
    async with session.begin() as sess:
        sess.add(SimpleParent(id=p.id, date=datetime(2023, 2, 13, 19, 4)))

    app = web.Application()
    app.router.add_get("/js", serve_js, name="js")

    # This is the setup required for aiohttp-admin.
    schema: aiohttp_admin.Schema = {
        "security": {
            "check_credentials": check_credentials,
            "secure": False
        },
        "resources": (
            {"model": SAResource(engine, Simple), "show_actions": (comp("CustomCloneButton"),)},
            {"model": SAResource(engine, SimpleParent)}
        ),
        "js_module": str(app.router["js"].url_for())
    }
    aiohttp_admin.setup(app, schema)

    return app

if __name__ == "__main__":
    web.run_app(create_app())
