import json
from datetime import date, datetime
from typing import Awaitable, Callable, Type, Union

import pytest
import sqlalchemy as sa
from aiohttp import web
from aiohttp.test_utils import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import aiohttp_admin
from _auth import check_credentials
from aiohttp_admin.backends.sqlalchemy import SAResource

_Login = Callable[[TestClient], Awaitable[dict[str, str]]]


def test_pk(base: Type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "dummy"
        id: Mapped[int] = mapped_column(primary_key=True)
        num: Mapped[str]

    r = SAResource(mock_engine, TestModel)
    assert r.name == "dummy"
    assert r.primary_key == "id"
    assert r.fields == {
        "id": {"type": "NumberField", "props": {}},
        "num": {"type": "TextField", "props": {}}
    }
    # Autoincremented PK should not be in create form
    assert r.inputs == {
        "id": {"type": "NumberInput", "show_create": False, "props": {},
               "validators": [("required",)]},
        "num": {"type": "TextInput", "show_create": True, "props": {},
                "validators": [("required",)]}
    }


def test_table(mock_engine: AsyncEngine) -> None:
    dummy_table = sa.Table("dummy", sa.MetaData(),
                           sa.Column("id", sa.Integer, primary_key=True),
                           sa.Column("num", sa.String(30)))

    r = SAResource(mock_engine, dummy_table)
    assert r.name == "dummy"
    assert r.primary_key == "id"
    assert r.fields == {
        "id": {"type": "NumberField", "props": {}},
        "num": {"type": "TextField", "props": {}}
    }
    # Autoincremented PK should not be in create form
    assert r.inputs == {
        "id": {"type": "NumberInput", "show_create": False, "props": {},
               "validators": [("required",)]},
        "num": {"type": "TextInput", "show_create": True, "props": {},
                "validators": [("maxLength", 30)]}
    }


def test_fk(base: Type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "dummy"
        id: Mapped[int] = mapped_column(primary_key=True)

    class TestChildModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "child"
        id: Mapped[int] = mapped_column(sa.ForeignKey(TestModel.id), primary_key=True)

    r = SAResource(mock_engine, TestChildModel)
    assert r.name == "child"
    assert r.primary_key == "id"
    assert r.fields == {"id": {"type": "ReferenceField", "props": {"reference": "dummy"}}}
    # PK with FK constraint should be shown in create form.
    assert r.inputs == {"id": {
        "type": "ReferenceInput", "show_create": True, "props": {"reference": "dummy"},
        "validators": [("required",)]}}


def test_relationship(base: Type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestMany(base):  # type: ignore[misc,valid-type]
        __tablename__ = "many"
        id: Mapped[int] = mapped_column(primary_key=True)
        ones: Mapped[list["TestOne"]] = relationship()  # noqa: F821

    class TestOne(base):  # type: ignore[misc,valid-type]
        __tablename__ = "one"
        id: Mapped[int] = mapped_column(primary_key=True)
        many_id: Mapped[int] = mapped_column(sa.ForeignKey(TestMany.id))

    r = SAResource(mock_engine, TestMany)
    assert r.name == "many"
    assert r.fields["ones"] == {
        "type": "ReferenceManyField",
        "props": {"children": {"id": {"props": {}, "type": "NumberField"}},
                  "label": "Ones", "reference": "one", "source": "id", "target": "many_id"}}
    assert "ones" not in r.inputs


def test_check_constraints(base: Type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestCC(base):  # type: ignore[misc,valid-type]
        __tablename__ = "test"
        pk: Mapped[int] = mapped_column(primary_key=True)
        default: Mapped[int] = mapped_column(default=5)
        server_default: Mapped[int] = mapped_column(server_default="4")
        nullable: Mapped[Union[int, None]]
        not_nullable: Mapped[int]
        max_length: Mapped[str] = mapped_column(sa.String(16))
        gt: Mapped[int] = mapped_column()
        gte: Mapped[int] = mapped_column()
        lt: Mapped[int] = mapped_column()
        lte: Mapped[Union[int, None]] = mapped_column()
        min_length: Mapped[str] = mapped_column()
        min_length_gt: Mapped[str] = mapped_column()
        regex: Mapped[str] = mapped_column()

        __table_args__ = (sa.CheckConstraint(gt > 3), sa.CheckConstraint(gte >= 3),
                          sa.CheckConstraint(lt < 3), sa.CheckConstraint(lte <= 3),
                          sa.CheckConstraint(sa.func.char_length(min_length) >= 5),
                          sa.CheckConstraint(sa.func.char_length(min_length_gt) > 5),
                          sa.CheckConstraint(sa.func.regexp(regex, r"abc.*")))

    r = SAResource(mock_engine, TestCC)

    f = r.inputs
    assert f["pk"]["validators"] == [("required",)]
    assert f["default"]["validators"] == []
    assert f["server_default"]["validators"] == []
    assert f["nullable"]["validators"] == []
    assert f["not_nullable"]["validators"] == [("required",)]
    assert f["max_length"]["validators"] == [("required",), ("maxLength", 16)]
    assert f["gt"]["validators"] == [("required",), ("minValue", 4)]
    assert f["gte"]["validators"] == [("required",), ("minValue", 3)]
    assert f["lt"]["validators"] == [("required",), ("maxValue", 2)]
    assert f["lte"]["validators"] == [("maxValue", 3)]
    assert f["min_length"]["validators"] == [("required",), ("minLength", 5)]
    assert f["min_length_gt"]["validators"] == [("required",), ("minLength", 6)]
    assert f["regex"]["validators"] == [("required",), ("regex", "abc.*")]


async def test_nonid_pk(base: Type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "test"
        num: Mapped[int] = mapped_column(primary_key=True)
        other: Mapped[str]

    r = SAResource(mock_engine, TestModel)
    assert r.name == "test"
    assert r.primary_key == "num"
    assert r.fields == {
        "num": {"type": "NumberField", "props": {}},
        "other": {"type": "TextField", "props": {}}
    }
    assert r.inputs == {
        "num": {"type": "NumberInput", "show_create": False, "props": {},
                "validators": [("required",)]},
        "other": {"type": "TextInput", "show_create": True, "props": {},
                  "validators": [("required",)]}
    }


async def test_id_nonpk(base: Type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class NotPK(base):  # type: ignore[misc,valid-type]
        __tablename__ = "notpk"
        name: Mapped[str] = mapped_column(primary_key=True)
        id: Mapped[int]

    class CompositePK(base):  # type: ignore[misc,valid-type]
        __tablename__ = "compound"
        id: Mapped[int] = mapped_column(primary_key=True)
        other: Mapped[int] = mapped_column(primary_key=True)

    with pytest.warns(UserWarning, match="A non-PK 'id' column is likely to break the admin."):
        SAResource(mock_engine, NotPK)
    # TODO: Support composite PK.
    # with pytest.warns(UserWarning, match="'id' column in a composite PK is likely to"
    #                   + " break the admin"):
    #     SAResource(mock_engine, CompositePK)


async def test_nonid_pk_api(
    base: DeclarativeBase, aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
    login: _Login
) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "test"
        num: Mapped[int] = mapped_column(primary_key=True)
        other: Mapped[str]

    app = web.Application()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    db = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)
    async with db.begin() as sess:
        sess.add(TestModel(num=5, other="foo"))
        sess.add(TestModel(num=8, other="bar"))

    schema: aiohttp_admin.Schema = {
        "security": {
            "check_credentials": check_credentials,
            "secure": False
        },
        "resources": ({"model": SAResource(engine, TestModel)},)
    }
    app["admin"] = aiohttp_admin.setup(app, schema)

    admin_client = await aiohttp_client(app)
    assert admin_client.app
    h = await login(admin_client)

    url = app["admin"].router["test_get_list"].url_for()
    p = {"pagination": json.dumps({"page": 1, "perPage": 10}),
         "sort": json.dumps({"field": "id", "order": "DESC"}), "filter": "{}"}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 8, "num": 8, "other": "bar"},
                                              {"id": 5, "num": 5, "other": "foo"}], "total": 2}

    url = app["admin"].router["test_get_one"].url_for()
    async with admin_client.get(url, params={"id": 8}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 8, "num": 8, "other": "bar"}}

    url = app["admin"].router["test_get_many"].url_for()
    async with admin_client.get(url, params={"ids": "[5, 8]"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 5, "num": 5, "other": "foo"},
                                              {"id": 8, "num": 8, "other": "bar"}]}

    url = app["admin"].router["test_create"].url_for()
    p = {"data": json.dumps({"num": 12, "other": "this"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 12, "num": 12, "other": "this"}}

    url = app["admin"].router["test_update"].url_for()
    p1 = {"id": 5, "data": json.dumps({"id": 5, "other": "that"}), "previousData": "{}"}
    async with admin_client.put(url, params=p1, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 5, "num": 5, "other": "that"}}


async def test_datetime(
    base: DeclarativeBase, aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
    login: _Login
) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "test"
        id: Mapped[int] = mapped_column(primary_key=True)
        date: Mapped[date]
        time: Mapped[datetime]

    app = web.Application()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    db = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)
    async with db.begin() as sess:
        sess.add(TestModel(date=date(2023, 4, 23), time=datetime(2023, 1, 2, 3, 4)))

    schema: aiohttp_admin.Schema = {
        "security": {
            "check_credentials": check_credentials,
            "secure": False
        },
        "resources": ({"model": SAResource(engine, TestModel)},)
    }
    app["admin"] = aiohttp_admin.setup(app, schema)

    admin_client = await aiohttp_client(app)
    assert admin_client.app
    h = await login(admin_client)

    url = app["admin"].router["test_get_one"].url_for()
    async with admin_client.get(url, params={"id": 1}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1, "date": "2023-04-23",
                                              "time": "2023-01-02 03:04:00"}}

    url = app["admin"].router["test_create"].url_for()
    p = {"data": json.dumps({"date": "2024-05-09", "time": "2020-11-12 03:04:05"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 2, "date": "2024-05-09",
                                              "time": "2020-11-12 03:04:05"}}
