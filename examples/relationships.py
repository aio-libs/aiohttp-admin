"""Example that demonstrates use of various foreign key relationships.

When running this file, admin will be accessible at /admin.
"""

from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import aiohttp_admin
from _models import Author, Base, Book
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
        sess.add(Author())
        author1 = Author()
        sess.add(author1)
    async with session.begin() as sess:
        sess.add(Book(author_id=author1.id, title="Book 1"))
        sess.add(Book(author_id=author1.id, title="Book 2"))
        sess.add(Book(author_id=author1.id, title="Another book"))

    app = web.Application()

    # This is the setup required for aiohttp-admin.
    schema: aiohttp_admin.Schema = {
        "security": {
            "check_credentials": check_credentials,
            "secure": False
        },
        "resources": (
            {"model": SAResource(engine, Author)},
            {"model": SAResource(engine, Book)}
        )
    }
    aiohttp_admin.setup(app, schema)

    return app

if __name__ == "__main__":
    web.run_app(create_app())
