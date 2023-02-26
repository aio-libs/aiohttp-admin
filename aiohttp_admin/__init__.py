import secrets
from typing import Optional

import aiohttp_security
import aiohttp_session
from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp_security import AbstractAuthorizationPolicy
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from pydantic import ValidationError, parse_obj_as

from .backends.abc import Permissions
from .routes import setup_resources, setup_routes
from .security import TokenIdentityPolicy
from .types import Schema, UserDetails

__all__ = ("Permissions", "Schema", "UserDetails", "setup")
__version__ = "0.1.0a0"


@web.middleware
async def pydantic_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    try:
        return await handler(request)
    except ValidationError as e:
        raise web.HTTPBadRequest(text=e.json(), content_type="application/json")


def setup(app: web.Application, schema: Schema, auth_policy: AbstractAuthorizationPolicy,  # type: ignore[no-any-unimported] # noqa: B950
          *, path: str = "/admin", secret: Optional[bytes] = None) -> web.Application:
    """Initialize the admin.

    Args:
        app - Parent application to add the admin sub app to.
        schema - Schema to define admin layout/behaviour.
        auth_policy - aiohttp-security auth policy.
        path - The path used when adding the admin sub app to app.
        secret - Cookie encryption key. If not provided, a random key is generated, which
            will result in users being logged out each time the app is restarted. To
            avoid this (or if using multiple servers) it is recommended to generate a
            random secret (e.g. secrets.token_bytes()) and save the value.

    Returns the admin application.
    """
    async def on_startup(admin: web.Application) -> None:
        """Configuration steps which require the application to be already configured.

        This is very awkward, as we need the nested function to be able to reference
        prefixed_subapp at the end of the setup. Once we have that object the app
        is frozen and we can't modify the app, in order to add this startup function.
        Therefore, we add this function first, then we can get the reference from the
        enclosing scope later.
        """
        storage._cookie_params["path"] = prefixed_subapp.canonical
        admin["state"]["urls"] = {
            "token": str(admin.router["token"].url_for()),
            "logout": str(admin.router["logout"].url_for())
        }

        def key(r: web.RouteDef) -> str:
            name: str = r.kwargs["name"]
            return name.removeprefix(m.name + "_")

        def value(r: web.RouteDef) -> tuple[str, str]:
            return (r.method, str(admin.router[r.kwargs["name"]].url_for()))

        for res in schema["resources"]:
            m = res["model"]
            admin["state"]["resources"][m.name]["urls"] = {key(r): value(r) for r in m.routes}

    schema = parse_obj_as(Schema, schema)
    if secret is None:
        secret = secrets.token_bytes()

    admin = web.Application()
    admin.middlewares.append(pydantic_middleware)
    admin.on_startup.append(on_startup)
    admin["check_credentials"] = schema["security"]["check_credentials"]
    admin["state"] = {"view": schema.get("view", {})}

    max_age = schema["security"].get("max_age")
    secure = schema["security"].get("secure", True)
    storage = EncryptedCookieStorage(
        secret, max_age=max_age, httponly=True, samesite="Strict", secure=secure)
    identity_policy = TokenIdentityPolicy(storage._fernet, schema)
    aiohttp_session.setup(admin, storage)
    aiohttp_security.setup(admin, identity_policy, auth_policy)

    setup_routes(admin)
    setup_resources(admin, schema)
    prefixed_subapp = app.add_subapp(path, admin)
    return admin
