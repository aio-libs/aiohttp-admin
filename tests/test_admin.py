import pytest
from aiohttp import web

import aiohttp_admin
from _auth import check_credentials
from _resources import DummyResource
from aiohttp_admin.types import comp, func


def test_path() -> None:
    app = web.Application()
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ()}
    admin = aiohttp_admin.setup(app, schema)

    assert str(admin.router["index"].url_for()) == "/admin"

    admin = aiohttp_admin.setup(app, schema, path="/another/admin")

    assert str(admin.router["index"].url_for()) == "/another/admin"


def test_js_module() -> None:
    app = web.Application()
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": (), "js_module": "/custom_js.js"}
    admin = aiohttp_admin.setup(app, schema)

    assert admin["state"]["js_module"] == "/custom_js.js"


def test_no_js_module() -> None:
    app = web.Application()
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ()}
    admin = aiohttp_admin.setup(app, schema)

    assert admin["state"]["js_module"] is None


def test_validators() -> None:
    dummy = DummyResource(
        "dummy",
        {"id": {"__type__": "component", "type": "NumberField", "props": {}}},
        {"id": {"__type__": "component", "type": "NumberInput",
                "props": {"validate": ({"__type__": "function", "name": "required", "args": ()},)},
                "show_create": True}},
        "id")
    app = web.Application()
    schema: aiohttp_admin.Schema = {
        "security": {"check_credentials": check_credentials},
        "resources": ({"model": dummy, "validators": {"id": (func("minValue", (3,)),)}},)}
    admin = aiohttp_admin.setup(app, schema)
    validators = admin["state"]["resources"]["dummy"]["inputs"]["id"]["props"]["validate"]
    assert validators == (func("required", ()), func("minValue", (3,)))
    assert ("minValue", 3) not in dummy.inputs["id"]["props"]["validate"]  # type: ignore[operator]


def test_re() -> None:
    test_re = DummyResource(
        "testre", {"id": comp("NumberField"), "value": comp("TextField")}, {}, "id")

    app = web.Application()
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ({"model": test_re},)}
    admin = aiohttp_admin.setup(app, schema)
    r = admin["permission_re"]

    assert r.fullmatch("admin.*")
    assert r.fullmatch("admin.view")
    assert r.fullmatch("~admin.edit")
    assert r.fullmatch("admin.testre.*")
    assert r.fullmatch("admin.testre.add")
    assert r.fullmatch("admin.testre.id.*")
    assert r.fullmatch("admin.testre.value.edit")
    assert r.fullmatch("~admin.testre.id.edit")
    assert r.fullmatch("admin.testre.edit|id=5")
    assert r.fullmatch('admin.testre.add|id=1|value="4"|value="7"')
    assert r.fullmatch('admin.testre.value.*|value="foo"')
    assert r.fullmatch("admin.testre.value.delete|id=5|id=3")

    assert r.fullmatch("testre.edit") is None
    assert r.fullmatch("admin.create") is None
    assert r.fullmatch("admin.nottest.*") is None
    assert r.fullmatch("admin.*|id=1") is None
    assert r.fullmatch("admin.testre.edit|other=5") is None
    assert r.fullmatch("admin.testre.value.*|value=unquoted") is None
    assert r.fullmatch("~admin.testre.edit|id=5") is None
    assert r.fullmatch('~admin.testre.value.delete|value="1"') is None


def test_display() -> None:
    app = web.Application()
    model = DummyResource(
        "test",
        {"id": comp("TextField"), "foo": comp("TextField")},
        {"id": comp("TextInput", {"validate": (func("required", ()),)}) | {"show_create": False},  # type: ignore[dict-item]
         "foo": comp("TextInput") | {"show_create": True}},  # type: ignore[dict-item]
        "id")
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ({"model": model, "display": ("foo",)},)}

    admin = aiohttp_admin.setup(app, schema)

    test_state = admin["state"]["resources"]["test"]
    assert test_state["list_omit"] == ("id",)
    assert test_state["inputs"]["id"]["props"] == {"validate": (func("required", ()),)}
    assert test_state["inputs"]["foo"]["props"] == {"alwaysOn": "alwaysOn"}


def test_display_invalid() -> None:
    app = web.Application()
    model = DummyResource("test", {"id": comp("TextField"), "foo": comp("TextField")}, {}, "id")
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ({"model": model, "display": ("bar",)},)}

    with pytest.raises(ValueError, match=r"Display includes non-existent field \('bar',\)"):
        aiohttp_admin.setup(app, schema)


def test_extra_props() -> None:
    app = web.Application()
    model = DummyResource(
        "test",
        {"id": comp("TextField", {"textAlign": "right", "placeholder": "foo"})},
        {"id": comp("TextInput", {"resettable": False, "type": "text"})
         | {"show_create": False}},  # type: ignore[dict-item]
        "id")
    schema: aiohttp_admin.Schema = {
        "security": {"check_credentials": check_credentials},
        "resources": ({
            "model": model,
            "field_props": {"id": {"textAlign": "left", "label": "Spam"}},
            "input_props": {"id": {"type": "email", "multiline": True}}
        },)}

    admin = aiohttp_admin.setup(app, schema)

    test_state = admin["state"]["resources"]["test"]
    assert test_state["fields"]["id"]["props"] == {"textAlign": "left", "placeholder": "foo",
                                                   "label": "Spam"}
    assert test_state["inputs"]["id"]["props"] == {"alwaysOn": "alwaysOn", "type": "email",
                                                   "multiline": True, "resettable": False}


def test_invalid_repr() -> None:
    app = web.Application()
    model = DummyResource("test", {"id": comp("TextField"), "foo": comp("TextField")}, {}, "id")
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ({"model": model, "repr": "bar"},)}

    with pytest.raises(ValueError, match=r"not a valid field name: bar"):
        aiohttp_admin.setup(app, schema)
