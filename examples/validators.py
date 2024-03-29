"""Minimal example with simple database models.

When running this file, admin will be accessible at /admin.
"""

import sqlalchemy as sa
from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

import aiohttp_admin
from aiohttp_admin.backends.sqlalchemy import SAResource
from aiohttp_admin.types import func, regex

JS = """
const odd = (value, allValues) => {
    if (value % 2 === 0)
        return "Votes must be an odd number";
    return undefined;
};

export const functions = {odd};
"""


class Base(DeclarativeBase):
    """Base model."""


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(sa.String(32))
    email: Mapped[str | None]
    note: Mapped[str | None]
    votes: Mapped[int] = mapped_column()

    __table_args__ = (sa.CheckConstraint(sa.func.char_length(username) >= 3),
                      sa.CheckConstraint(votes >= 1), sa.CheckConstraint(votes < 6),
                      sa.CheckConstraint(votes % 2 == 1))


async def check_credentials(username: str, password: str) -> bool:
    return username == "admin" and password == "admin"


async def serve_js(request: web.Request) -> web.Response:
    return web.Response(text=JS, content_type="text/javascript")


async def create_app() -> web.Application:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session = async_sessionmaker(engine, expire_on_commit=False)

    # Create some sample data
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session.begin() as sess:
        sess.add(User(username="Foo", votes=5))
        sess.add(User(username="Spam", votes=1, note="Second user"))

    app = web.Application()
    app.router.add_get("/js", serve_js, name="js")

    # This is the setup required for aiohttp-admin.
    schema: aiohttp_admin.Schema = {
        "security": {
            "check_credentials": check_credentials,
            "secure": False
        },
        "resources": ({"model": SAResource(engine, User),
                       "validators": {User.username.name: (func("regex",
                                                                (regex(r"^[A-Z][a-z]+$"),)),),
                                      User.email.name: (func("email", ()),),
                                      # Custom validator from our JS module.
                                      # Min/Max validators are automatically included.
                                      User.votes.name: (func("odd"),)}},),
        # Use our JS module to include our custom validator.
        "js_module": str(app.router["js"].url_for())
    }
    aiohttp_admin.setup(app, schema)

    return app

if __name__ == "__main__":
    web.run_app(create_app())
