from aiohttp import web
import pytest

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


def test_display() -> None:
    app = web.Application()
    model = DummyResource("test", {"id": {"type": "TextField", "props": {}},
                                   "foo": {"type": "TextField", "props": {}}}, {}, "id")
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ({"model": model, "display": ("foo",)},)}

    admin = aiohttp_admin.setup(app, schema)

    assert admin["state"]["resources"]["test"]["list_omit"] == ("id",)


def test_display_invalid() -> None:
    app = web.Application()
    model = DummyResource("test", {"id": {"type": "TextField", "props": {}},
                                   "foo": {"type": "TextField", "props": {}}}, {}, "id")
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ({"model": model, "display": ("bar",)},)}

    with pytest.raises(ValueError, match=r"Display includes non-existent field \('bar',\)"):
        admin = aiohttp_admin.setup(app, schema)
