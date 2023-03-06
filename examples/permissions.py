"""Example to demonstrate usage of permissions.

When running this file, admin will be accessible at /admin.
Check below for valid usernames (and their respective permissions),
login will work with any password.
"""

import json
from datetime import datetime
from enum import Enum

from aiohttp import ChainMapProxy, web
from aiohttp_security import AbstractAuthorizationPolicy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

import aiohttp_admin
from _models import Base, Simple, SimpleParent
from aiohttp_admin import Permissions, UserDetails, has_permission
from aiohttp_admin.backends.sqlalchemy import SAResource


class User(Base):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(primary_key=True)
    permissions: Mapped[str]


class AuthPolicy(AbstractAuthorizationPolicy):  # type: ignore[misc,no-any-unimported]
    def __init__(self, app: web.Application):
        super().__init__()
        self.app = app

    async def authorized_userid(self, identity: str) -> str | None:
        async with self.app["db"]() as sess:
            user = await sess.get(User, identity)
            return None if user is None else user.username

    async def permits(self, identity: str | None, permission: str | Enum,
                      context: object = None) -> bool:
        async with self.app["db"]() as sess:
            user = await sess.get(User, identity)
            return has_permission(permission, json.loads(user.permissions))


async def check_credentials(app: ChainMapProxy, username: str, password: str) -> bool:
    """Allow login to any user account regardless of password."""
    async with app["db"]() as sess:
        user = await sess.get(User, username.lower())
        return user is not None


async def identity_callback(request: web.Request, identity: str) -> UserDetails:
    async with request.config_dict["db"]() as sess:
        user = await sess.get(User, identity)
        return {"permissions": json.loads(user.permissions), "fullName": user.username.title()}


async def create_app() -> web.Application:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session = async_sessionmaker(engine, expire_on_commit=False)

    # Create some sample data
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session.begin() as sess:
        # Users with various permissions.
        sess.add(User(username="admin", permissions=json.dumps(tuple(Permissions))))
        sess.add(User(username="view", permissions=json.dumps((Permissions.view,))))
        sess.add(User(username="add", permissions=json.dumps(
            (Permissions.view, Permissions.add,))))
        sess.add(User(username="edit", permissions=json.dumps(
            (Permissions.view, Permissions.edit))))
        sess.add(User(username="delete", permissions=json.dumps(
            (Permissions.view, Permissions.delete))))
        sess.add(User(username="simple", permissions=json.dumps(("admin.simple.*",))))
        sess.add(User(username="mixed", permissions=json.dumps(
            ("admin.simple.view", "admin.simple.edit", "admin.parent.view"))))
    async with session.begin() as sess:
        sess.add(Simple(num=5, value="first"))
        p = Simple(num=82, optional_num=12, value="with child")
        sess.add(p)
    async with session.begin() as sess:
        sess.add(SimpleParent(id=p.id, date=datetime(2023, 2, 13, 19, 4)))

    app = web.Application()
    app["db"] = session

    # This is the setup required for aiohttp-admin.
    schema: aiohttp_admin.Schema = {
        "security": {
            "check_credentials": check_credentials,
            "identity_callback": identity_callback,
            "secure": False
        },
        "resources": (
            {"model": SAResource(engine, Simple)},
            {"model": SAResource(engine, SimpleParent)}
        )
    }
    aiohttp_admin.setup(app, schema, AuthPolicy(app))

    return app

if __name__ == "__main__":
    web.run_app(create_app())
