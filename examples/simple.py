"""Minimal example with simple database models.

When running this file, admin will be accessible at /admin.
"""

from datetime import datetime

from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import aiohttp_admin
from _models import Base, Simple, SimpleParent
from aiohttp_admin.backends.sqlalchemy import SAResource


async def check_credentials(username: str, password: str) -> bool:
    return username == "admin" and password == "admin"


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

    # This is the setup required for aiohttp-admin.
    schema: aiohttp_admin.Schema = {
        "security": {
            "check_credentials": check_credentials,
            "secure": False
        },
        "resources": (
            {"model": SAResource(engine, Simple)},
            {"model": SAResource(engine, SimpleParent)}
        )
    }
    aiohttp_admin.setup(app, schema)

    return app

if __name__ == "__main__":
    web.run_app(create_app())
