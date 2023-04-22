import pytest
from aiohttp import web

import aiohttp_admin
from _auth import check_credentials
from _resources import DummyResource


def test_path() -> None:
    app = web.Application()
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ()}
    admin = aiohttp_admin.setup(app, schema)

    assert str(admin.router["index"].url_for()) == "/admin"

    admin = aiohttp_admin.setup(app, schema, path="/another/admin")

    assert str(admin.router["index"].url_for()) == "/another/admin"


def test_validators() -> None:
    dummy = DummyResource(
        "dummy", {"id": {"type": "NumberField", "props": {}}},
        {"id": {"type": "NumberInput", "props": {}, "show_create": True,
         "validators": (("required",),)}}, "id")
    app = web.Application()
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ({"model": dummy,
                                                   "validators": {"id": (("minValue", 3),)}},)}
    admin = aiohttp_admin.setup(app, schema)
    validators = admin["state"]["resources"]["dummy"]["inputs"]["id"]["validators"]
    # TODO(Pydantic2): Should be int 3 in both lines.
    assert validators == (("required",), ("minValue", "3"))
    assert ("minValue", "3") not in dummy.inputs["id"]["validators"]

    # Invalid validator
    schema = {"security": {"check_credentials": check_credentials},
              "resources": ({"model": dummy, "validators": {"id": (("bad", 3),)}},)}
    with pytest.raises(ValueError, match="validators must be one of"):
        aiohttp_admin.setup(app, schema)


def test_re() -> None:
    test_re = DummyResource("testre", {"id": {"type": "NumberField", "props": {}},
                                       "value": {"type": "TextField", "props": {}}}, {}, "id")

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
        {"id": {"type": "TextField", "props": {}}, "foo": {"type": "TextField", "props": {}}},
        {"id": {"type": "TextInput", "props": {}, "show_create": False,
         "validators": (("required",),)},
         "foo": {"type": "TextInput", "props": {}, "show_create": True, "validators": ()}},
        "id")
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ({"model": model, "display": ("foo",)},)}

    admin = aiohttp_admin.setup(app, schema)

    test_state = admin["state"]["resources"]["test"]
    assert test_state["list_omit"] == ("id",)
    assert test_state["inputs"]["id"]["props"] == {}
    assert test_state["inputs"]["foo"]["props"] == {"alwaysOn": "alwaysOn"}


def test_display_invalid() -> None:
    app = web.Application()
    model = DummyResource("test", {"id": {"type": "TextField", "props": {}},
                                   "foo": {"type": "TextField", "props": {}}}, {}, "id")
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ({"model": model, "display": ("bar",)},)}

    with pytest.raises(ValueError, match=r"Display includes non-existent field \('bar',\)"):
        aiohttp_admin.setup(app, schema)
