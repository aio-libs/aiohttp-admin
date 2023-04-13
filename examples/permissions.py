"""Example to demonstrate usage of permissions.

When running this file, admin will be accessible at /admin.
Check near the bottom of the file for valid usernames (and their respective permissions),
login will work with any password.
"""

import json
from datetime import datetime
from functools import partial

from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

import aiohttp_admin
from _models import Base, Simple, SimpleParent
from aiohttp_admin import Permissions, UserDetails
from aiohttp_admin.backends.sqlalchemy import SAResource


class User(Base):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(primary_key=True)
    permissions: Mapped[str]


async def check_credentials(app: web.Application, username: str, password: str) -> bool:
    """Allow login to any user account regardless of password."""
    async with app["db"]() as sess:
        user = await sess.get(User, username.lower())
        return user is not None


async def identity_callback(app: web.Application, identity: str) -> UserDetails:
    async with app["db"]() as sess:
        user = await sess.get(User, identity)
        return {"permissions": json.loads(user.permissions), "fullName": user.username.title()}


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
        sess.add(Simple(num=5, value="second"))
        sess.add(Simple(num=5, value="3"))
        sess.add(Simple(num=5, optional_num=42, value="4"))
        sess.add(Simple(num=5, value="5"))
    async with session.begin() as sess:
        sess.add(SimpleParent(id=p.id, date=datetime(2023, 2, 13, 19, 4)))

    app = web.Application()
    app["db"] = session

    # This is the setup required for aiohttp-admin.
    schema: aiohttp_admin.Schema = {
        "security": {
            "check_credentials": partial(check_credentials, app),
            "identity_callback": partial(identity_callback, app),
            "secure": False
        },
        "resources": (
            {"model": SAResource(engine, Simple),
             "bulk_update": {"Set to 7": {"optional_num": 7}}},
            {"model": SAResource(engine, SimpleParent)}
        )
    }
    admin = aiohttp_admin.setup(app, schema)

    # Create users with various permissions.
    async with session.begin() as sess:
        sess.add(User(username="admin", permissions=json.dumps(tuple(Permissions))))
        sess.add(User(username="view", permissions=json.dumps((Permissions.view,))))
        sess.add(User(username="add", permissions=json.dumps(
            (Permissions.view, Permissions.add,))))
        sess.add(User(username="edit", permissions=json.dumps(
            (Permissions.view, Permissions.edit))))
        sess.add(User(username="delete", permissions=json.dumps(
            (Permissions.view, Permissions.delete))))
        users = {
            "simple": ("admin.simple.*",),
            "mixed": ("admin.simple.view", "admin.simple.edit", "admin.parent.view"),
            "negated": ("admin.*", "~admin.parent.*", "~admin.simple.edit"),
            "field": ("admin.*", "~admin.simple.optional_num.*"),
            "field_edit": ("admin.*", "~admin.simple.optional_num.edit"),
            "filter": ("admin.*", "admin.simple.*|num=5"),
            "filter_edit": ("admin.*", "admin.simple.edit|num=5"),
            "filter_add": ("admin.*", "admin.simple.add|num=5"),
            "filter_delete": ("admin.*", "admin.simple.delete|num=5"),
            "filter_field": ("admin.*", "admin.simple.optional_num.*|num=5"),
            "filter_field_edit": ("admin.*", "admin.simple.optional_num.edit|num=5")
        }
        for name, permissions in users.items():
            if any(admin["permission_re"].fullmatch(p) is None for p in permissions):
                raise ValueError("Not a valid permission.")
            sess.add(User(username=name, permissions=json.dumps(permissions)))

    return app

if __name__ == "__main__":
    web.run_app(create_app())
