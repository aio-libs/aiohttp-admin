from abc import abstractmethod
from enum import Enum

from aiohttp_security import AbstractAuthorizationPolicy
from aiohttp_security import AbstractIdentityPolicy
from aiohttp_security import permits
from aiohttp_security.api import AUTZ_KEY

from .exceptions import JsonForbiddenError


__all__ = ["Permissions", "require", "authorize"]


class Permissions(str, Enum):
    view = "aiohttp_admin.view"
    edit = "aiohttp_admin.edit"
    add = "aiohttp_admin.add"
    delete = "aiohttp_admin.delete"


class AdminAbstractAuthorizationPolicy(AbstractAuthorizationPolicy):

    @abstractmethod
    async def check_credential(self, identity, password):  # pragma: no cover
        pass


async def require(request, permission):
    has_perm = await permits(request, permission)
    if not has_perm:
        msg = 'User has no permission {}'.format(permission)
        raise JsonForbiddenError(msg)


async def authorize(request, username, password):
    autz_policy = request.app.get(AUTZ_KEY)
    assert autz_policy, "aiohttp_security should inited first"
    is_user = await autz_policy.check_credential(username, password)
    if not is_user:
        msg = "Wrong username or password"
        raise JsonForbiddenError(msg)
    return is_user


class DummyAuthPolicy(AdminAbstractAuthorizationPolicy):

    def __init__(self, username, password, permissions=None):
        self._username = username
        self._password = password
        self._permissions = permissions or [p for p in Permissions]

    async def authorized_userid(self, identity):
        user_id = None
        if identity == self._username:
            user_id = 0
        return user_id

    async def permits(self, identity, permission, context=None):
        if identity is None:
            return False
        is_user = self._username == identity
        is_perm = permission in self._permissions
        return is_user and is_perm

    async def check_credential(self, identity, password):
        is_user = self._username == identity
        is_pass = self._password == password
        return is_user and is_pass


class DummyTokenIdentityPolicy(AbstractIdentityPolicy):

    async def identify(self, request):
        # validate token
        identity = request.headers.get("Authorization")
        return identity

    async def remember(self, request, response, identity, **kwargs):
        # save token in storage and reply to client
        response.headers['X-Token'] = identity

    async def forget(self, request, response):
        token = request.headers.get("Authorization")
        # destroy token,  remove it from storage
        assert token
