from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

import aiohttp_admin
from _auth import check_credentials
from aiohttp_admin.backends.sqlalchemy import SAResource


def test_path() -> None:
    app = web.Application()
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ()}
    admin = aiohttp_admin.setup(app, schema)

    assert str(admin.router["index"].url_for()) == "/admin"

    admin = aiohttp_admin.setup(app, schema, path="/another/admin")

    assert str(admin.router["index"].url_for()) == "/another/admin"


def test_re(base: type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestRE(base):  # type: ignore[misc,valid-type]
        __tablename__ = "testre"
        id: Mapped[int] = mapped_column(primary_key=True)
        value: Mapped[str]

    app = web.Application()
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ({"model": SAResource(mock_engine, TestRE)},)}
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
