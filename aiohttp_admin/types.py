import sys
from collections.abc import Callable, Collection, Sequence
from typing import Any, Awaitable, Literal, Mapping, Optional

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class ComponentState(TypedDict):
    __type__: Literal["component"]
    type: str
    props: dict[str, object]


class FunctionState(TypedDict):
    __type__: Literal["function"]
    name: str
    args: Optional[Sequence[object]]


class RegexState(TypedDict):
    __type__: Literal["regexp"]
    value: str


class InputState(ComponentState):
    # Whether to show this input in the create form.
    show_create: bool


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
    validators: dict[str, Sequence[FunctionState]]
    # Custom props to add to fields.
    field_props: dict[str, dict[str, Any]]
    # Custom props to add to inputs.
    input_props: dict[str, dict[str, Any]]
    # Custom components to add to the actions in the show view.
    show_actions: Sequence[ComponentState]


class Resource(_Resource):
    # The admin resource model.
    model: Any  # TODO(pydantic): AbstractAdminResource


class _Schema(TypedDict, total=False):
    view: _ViewSchema
    js_module: str


class Schema(_Schema):
    security: _SecuritySchema
    resources: Sequence[Resource]


class _ResourceState(TypedDict):
    display: Sequence[str]
    fields: dict[str, ComponentState]
    inputs: dict[str, InputState]
    show_actions: Sequence[ComponentState]
    repr: str
    icon: Optional[str]
    urls: dict[str, tuple[str, str]]  # (method, url)
    bulk_update: dict[str, dict[str, Any]]


class State(TypedDict):
    resources: dict[str, _ResourceState]
    urls: dict[str, str]
    view: _ViewSchema
    js_module: Optional[str]


def comp(t: str, props: Optional[Mapping[str, object]] = None) -> ComponentState:
    """Use a component of type t with the given props."""
    return {"__type__": "component", "type": t, "props": dict(props or {})}


def func(name: str, args: Optional[Sequence[object]] = None) -> FunctionState:
    """Use the function with matching name.

    If args are provided, the function will be called with those arguments.
    Otherwise, the function itself will be passed in the frontend.
    e.g. To use the 'required' validator, use func("required", ())
         Or, to pass a custom function directly as a prop, use func("myFunction")
    """
    return {"__type__": "function", "name": name, "args": args}


def regex(value: str) -> RegexState:
    """Convert value to a RegExp object on the frontend."""
    return {"__type__": "regexp", "value": value}
