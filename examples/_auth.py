"""Dummy auth code for a basic admin:admin login."""

from enum import Enum

from aiohttp import ChainMapProxy, web
from aiohttp_security import AbstractAuthorizationPolicy

from aiohttp_admin import Permissions, UserDetails


class DummyAuthPolicy(AbstractAuthorizationPolicy):
    async def authorized_userid(self, identity: str) -> str | None:
        return identity if identity == "admin" else None

    async def permits(self, identity: str | None, permission: str | Enum, context: object = None) -> bool:
        return identity == "admin"


async def check_credentials(app: ChainMapProxy, username: str, password: str) -> bool:
    """Return True if username and password are for a valid login, False otherwise."""
    return username == "admin" and password == "admin"

async def identity_callback(request: web.Request, identity: str) -> UserDetails:
    return {"permissions": tuple(Permissions)}  # All permissions
