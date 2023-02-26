from typing import Any, Awaitable, Callable, Optional, Sequence, TypedDict

from aiohttp import ChainMapProxy
from aiohttp import web

from .backends.abc import FieldState, InputState


class _IdentityDict(TypedDict, total=False):
    avatar: str


class IdentityDict(_IdentityDict):
    auth: str
    fullName: str
    permissions: Sequence[str]


class UserDetails(TypedDict, total=False):
    # https://marmelab.com/react-admin/AuthProviderWriting.html#getidentity
    fullName: str
    avatar: str
    # https://marmelab.com/react-admin/AuthProviderWriting.html#getpermissions
    permissions: Sequence[str]


class __SecuritySchema(TypedDict, total=False):
    # Callback that receives request and identity and should return user details
    # which the admin can use.
    identity_callback: Callable[[web.Request, str], Awaitable[UserDetails]]
    # max_age value for cookies/tokens, defaults to None.
    max_age: Optional[int]
    # Secure flag for cookies, defaults to True.
    secure: bool


class _SecuritySchema(__SecuritySchema):
    # Callback that receives request.config_dict, username and password and returns
    # True if authorised, False otherwise.
    check_credentials: Callable[[ChainMapProxy, str, str], Awaitable[bool]]


class _ViewSchema(TypedDict, total=False):
    # Path to favicon.
    icon: str
    # Name for the project (shown in the title), defaults to the package name.
    name: str


class _Resource(TypedDict, total=False):
    # List of field names that should be shown in the list view.
    display: Sequence[str]
    # name of the field that should be used for repr
    # (e.g. when displaying a foreign key reference).
    repr: str


class Resource(_Resource):
    # The admin resource model.
    model: Any  # TODO(pydantic): AbstractAdminResource


class _Schema(TypedDict, total=False):
    view: _ViewSchema


class Schema(_Schema):
    security: _SecuritySchema
    resources: Sequence[Resource]


class _ResourceState(TypedDict):
    display: Sequence[str]
    fields: dict[str, FieldState]
    inputs: dict[str, InputState]
    repr: str
    urls: dict[str, tuple[str, str]]  # (method, url)


class State(TypedDict):
    resources: dict[str, _ResourceState]
    urls: dict[str, str]
    view: _ViewSchema
