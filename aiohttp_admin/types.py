from collections.abc import Collection
from typing import Any, Awaitable, Callable, Optional, Sequence, TypedDict, Union


class FieldState(TypedDict):
    type: str
    props: dict[str, object]


class InputState(FieldState):
    # Whether to show this input in the create form.
    show_create: bool
    # Validators to add to the input. Each validator is the name of the validator
    # function, followed by arguments for that function. e.g. ("minValue", 5)
    validators: Sequence[Sequence[Union[str, int]]]


class _IdentityDict(TypedDict, total=False):
    avatar: str


class IdentityDict(_IdentityDict):
    auth: str
    fullName: str
    permissions: dict[str, dict[str, list[object]]]


class UserDetails(TypedDict, total=False):
    # https://marmelab.com/react-admin/AuthProviderWriting.html#getidentity
    fullName: str
    avatar: str
    # https://marmelab.com/react-admin/AuthProviderWriting.html#getpermissions
    permissions: Collection[str]


class __SecuritySchema(TypedDict, total=False):
    # Callback that receives identity and should return user details for the admin to use.
    identity_callback: Callable[[str], Awaitable[UserDetails]]
    # max_age value for cookies/tokens, defaults to None.
    max_age: Optional[int]
    # Secure flag for cookies, defaults to True.
    secure: bool


class _SecuritySchema(__SecuritySchema):
    # Callback that receives request.config_dict, username and password and returns
    # True if authorised, False otherwise.
    check_credentials: Callable[[str, str], Awaitable[bool]]


class _ViewSchema(TypedDict, total=False):
    # Path to favicon.
    icon: str
    # Name for the project (shown in the title), defaults to the package name.
    name: str


class _Resource(TypedDict, total=False):
    # List of field names that should be shown in the list view by default.
    display: Sequence[str]
    # Display label in admin.
    label: str
    # URL path to custom icon.
    icon: str
    # name of the field that should be used for repr
    # (e.g. when displaying a foreign key reference).
    repr: str
    # Bulk update actions (which appear when selecting rows in the list view).
    # Format: {"Button Label": {"field_to_update": "value_to_set"}}
    # e.g. {"Reset Views": {"views": 0}}
    bulk_update: dict[str, dict[str, Any]]
    # Custom validators to add to inputs.
    validators: dict[str, Sequence[Sequence[Union[str, int]]]]


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
    icon: Optional[str]
    urls: dict[str, tuple[str, str]]  # (method, url)
    bulk_update: dict[str, dict[str, Any]]


class State(TypedDict):
    resources: dict[str, _ResourceState]
    urls: dict[str, str]
    view: _ViewSchema
