import json
from typing import Optional

from aiohttp import web
from aiohttp_security import SessionIdentityPolicy
from cryptography.fernet import Fernet, InvalidToken
from pydantic import Json, ValidationError, parse_obj_as

from .types import IdentityDict, Schema, UserDetails


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
            user_details: UserDetails = {}
        else:
            user_details = await self._identity_callback(request, identity)
            if "auth" in user_details:
                raise ValueError("Callback should not return a dict with 'auth' key.")

        auth = self._fernet.encrypt(identity.encode("utf-8")).decode("utf-8")
        identity_dict: IdentityDict = {"auth": auth, "fullName": "Admin user", "permissions": ()}
        # https://github.com/python/mypy/issues/6462
        identity_dict.update(user_details)  # type: ignore[typeddict-item]
        return identity_dict
