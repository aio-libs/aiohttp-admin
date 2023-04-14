import json
from collections.abc import Collection
from enum import Enum
from typing import Mapping, Optional, Sequence, Union

from aiohttp import web
from aiohttp_security import AbstractAuthorizationPolicy, SessionIdentityPolicy
from cryptography.fernet import Fernet, InvalidToken
from pydantic import Json, ValidationError, parse_obj_as

from .types import IdentityDict, Schema, UserDetails


class Permissions(str, Enum):
    view = "admin.view"
    edit = "admin.edit"
    add = "admin.add"
    delete = "admin.delete"
    all = "admin.*"


def has_permission(p: Union[str, Enum], permissions: Mapping[str, Mapping[str, Sequence[object]]],
                   context: Optional[Mapping[str, object]]) -> bool:
    # TODO(PY311): StrEnum
    *parts, ptype = p.split(".")  # type: ignore[union-attr]

    # Negative permissions.
    for i in range(len(parts), 0, -1):
        for t in (ptype, "*"):
            perm = ".".join((*parts[:i], t))
            if "~" + perm in permissions:
                return False

    # Positive permissions.
    for i in range(len(parts), 0, -1):
        for t in (ptype, "*"):
            perm = ".".join((*parts[:i], t))
            if perm in permissions:
                if not context:
                    return True

                filters = permissions[perm]
                for attr, vals in filters.items():
                    if context.get(attr) not in vals:
                        return False
                return True
    return False


def permissions_as_dict(permissions: Collection[str]) -> dict[str, dict[str, list[object]]]:
    p_dict: dict[str, dict[str, list[object]]] = {}
    for p in permissions:
        perm, *filters = p.split("|")
        p_dict[perm] = {}
        for f in filters:
            k, v = f.split("=", maxsplit=1)
            p_dict[perm].setdefault(k, []).append(json.loads(v))
    return p_dict


class AdminAuthorizationPolicy(AbstractAuthorizationPolicy):  # type: ignore[misc,no-any-unimported]
    def __init__(self, schema: Schema):
        super().__init__()
        self._identity_callback = schema["security"].get("identity_callback")

    async def authorized_userid(self, identity: str) -> str:
        return identity

    async def permits(self, identity: Optional[str], permission: Union[str, Enum],
                      context: tuple[web.Request, Optional[Mapping[str, object]]]) -> bool:
        if identity is None:
            return False

        try:
            request, record = context
        except (TypeError, ValueError):
            raise TypeError("Context must be `(request, record)` or `(request, None)`")

        permissions: Optional[Collection[str]] = request.get("aiohttpadmin_permissions")
        if permissions is None:
            if self._identity_callback is None:
                permissions = (Permissions.all,)
            else:
                user = await self._identity_callback(identity)
                permissions = user["permissions"]
            # Cache permissions per request to avoid potentially dozens of DB calls.
            request["aiohttpadmin_permissions"] = permissions
        return has_permission(permission, permissions_as_dict(permissions), record)


class TokenIdentityPolicy(SessionIdentityPolicy):  # type: ignore[misc,no-any-unimported]
    def __init__(self, fernet: Fernet, schema: Schema):
        super().__init__()
        self._fernet = fernet
        config = schema["security"]
        self._identity_callback = config.get("identity_callback")
        self._max_age = config.get("max_age")

    async def identify(self, request: web.Request) -> Optional[str]:
        """Return the identity of an authorised user."""
        # Validate JS token
        hdr = request.headers.get("Authorization")
        try:
            identity_data = parse_obj_as(Json[IdentityDict], hdr)
        except ValidationError:
            return None

        auth = identity_data["auth"].encode("utf-8")
        try:
            token_identity = self._fernet.decrypt(auth, ttl=self._max_age).decode("utf-8")
        except InvalidToken:
            return None

        # Validate cookie token
        cookie_identity = await super().identify(request)

        # Both identites must match.
        return token_identity if token_identity == cookie_identity else None

    async def remember(self, request: web.Request, response: web.Response,
                       identity: str, **kwargs: object) -> None:
        """Send auth tokens to client for authentication."""
        # For proper security we send a token for JS to store and an HTTP only cookie:
        # https://www.redotheweb.com/2015/11/09/api-security.html
        # Send token that will be saved in local storage by the JS client.
        response.headers["X-Token"] = json.dumps(await self.user_identity_dict(request, identity))
        # Send httponly cookie, which will be invisible to JS.
        await super().remember(request, response, identity, **kwargs)

    async def forget(self, request: web.Request, response: web.Response) -> None:
        """Delete session cookie (JS client should choose to delete its token)."""
        await super().forget(request, response)

    async def user_identity_dict(self, request: web.Request, identity: str) -> IdentityDict:
        """Create the identity information sent back to the admin client.

        The 'auth' key will be used for the server authentication, everything else is
        just information that the client can use. For example, 'permissions' will be
        returned by the react-admin's getPermissions() and some values like
        'fullName' or 'avatar' will be automatically used:
            https://marmelab.com/react-admin/AuthProviderWriting.html#getidentity

        All details (except auth) can be specified using the identity callback.
        """
        if self._identity_callback is None:
            user_details: UserDetails = {"permissions": (Permissions.all,)}
        else:
            user_details = await self._identity_callback(identity)
            if "auth" in user_details:
                raise ValueError("Callback should not return a dict with 'auth' key.")

        auth = self._fernet.encrypt(identity.encode("utf-8")).decode("utf-8")
        identity_dict: IdentityDict = {"auth": auth, "fullName": "Admin user", "permissions": {}}
        # https://github.com/python/mypy/issues/6462
        identity_dict.update(user_details)  # type: ignore[typeddict-item]
        identity_dict["permissions"] = permissions_as_dict(user_details["permissions"])

        return identity_dict
