from enum import Enum

from aiohttp import ChainMapProxy, web
from aiohttp_security import AbstractAuthorizationPolicy

from aiohttp_admin import Permissions, UserDetails

async def check_credentials(app: ChainMapProxy, username: str, password: str) -> bool:
    return username == "admin" and password == "admin123"

async def identity_callback(request: web.Request, identity: str) -> UserDetails:
    return {"permissions": tuple(Permissions)}


class DummyAuthPolicy(AbstractAuthorizationPolicy):
    async def authorized_userid(self, identity: str) -> str | None:
        return identity if identity == "admin" else None

    async def permits(self, identity: str | None, permission: str | Enum, context: object = None) -> bool:
        return identity == "admin"
