import json
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from typing import Optional, Union

import pytest
import sqlalchemy as sa
from aiohttp import web
from aiohttp.test_utils import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.types import TypeDecorator

import aiohttp_admin
from _auth import check_credentials
from aiohttp_admin.backends.sqlalchemy import FIELD_TYPES, SAResource, permission_for
from aiohttp_admin.types import comp, func, regex

_Login = Callable[[TestClient], Awaitable[dict[str, str]]]


def test_no_subtypes() -> None:
    """We don't want any subtypes in the lookup, as this would depend on test ordering."""
    assert all({TypeEngine, TypeDecorator} & set(t.__bases__) for t in FIELD_TYPES)


def test_pk(base: type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "dummy"
        id: Mapped[int] = mapped_column(primary_key=True)
        num: Mapped[str]

    r = SAResource(mock_engine, TestModel)
    assert r.name == "dummy"
    assert r.primary_key == "id"
    assert r.fields == {"id": comp("NumberField", {"source": "id"}),
                        "num": comp("TextField", {"source": "num", "fullWidth": True,
                                                  "multiline": True})}
    # Autoincremented PK should not be in create form
    assert r.inputs == {
        "id": comp("NumberInput", {"source": "id", "validate": [func("required", ())]})
        | {"show_create": False},
        "num": comp("TextInput", {
            "source": "num", "fullWidth": True, "multiline": True,
            "validate": [func("required", ())]})
        | {"show_create": True}
    }


def test_table(mock_engine: AsyncEngine) -> None:
    dummy_table = sa.Table("dummy", sa.MetaData(),
                           sa.Column("id", sa.Integer, primary_key=True),
                           sa.Column("num", sa.String(30)))

    r = SAResource(mock_engine, dummy_table)
    assert r.name == "dummy"
    assert r.primary_key == "id"
    assert r.fields == {
        "id": comp("NumberField", {"source": "id"}),
        "num": comp("TextField", {"source": "num"})
    }
    # Autoincremented PK should not be in create form
    assert r.inputs == {
        "id": comp("NumberInput", {"source": "id", "validate": [func("required", ())]})
        | {"show_create": False},
        "num": comp("TextInput", {"source": "num", "validate": [func("maxLength", (30,))]})
        | {"show_create": True}
    }


def test_extra_props(base: type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "dummy"
        id: Mapped[int] = mapped_column(primary_key=True)
        num: Mapped[str] = mapped_column(sa.String(128), comment="Foo", default="Bar")

    r = SAResource(mock_engine, TestModel)
    assert r.fields["num"]["props"] == {
        "source": "num", "fullWidth": True, "multiline": True, "placeholder": "Bar",
        "helperText": "Foo"}
    assert r.inputs["num"]["props"] == {
        "source": "num", "fullWidth": True, "multiline": True, "placeholder": "Bar",
        "helperText": "Foo", "validate": [func("maxLength", (128,))]}


async def test_binary(
    base: DeclarativeBase, aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
    login: _Login
) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "test"
        id: Mapped[int] = mapped_column(primary_key=True)
        binary: Mapped[bytes]

    app = web.Application()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    db = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)
    async with db.begin() as sess:
        sess.add(TestModel(binary=b"foo"))
        sess.add(TestModel(binary=b"\x01\xFF\x02"))

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
        assert await resp.json() == {"data": {"id": "1", "binary": "foo"}}

    async with admin_client.get(url, params={"id": 2}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": "2", "binary": "\x01�\x02"}}


def test_fk(base: type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "dummy"
        id: Mapped[int] = mapped_column(primary_key=True)

    class TestChildModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "child"
        id: Mapped[int] = mapped_column(sa.ForeignKey(TestModel.id), primary_key=True)

    r = SAResource(mock_engine, TestChildModel)
    assert r.name == "child"
    assert r.primary_key == "id"
    assert r.fields == {"id": comp("ReferenceField",
                                   {"reference": "dummy", "source": "id", "target": "id"})}
    # PK with FK constraint should be shown in create form.
    assert r.inputs == {"id": comp(
        "ReferenceInput",
        {"validate": [func("required", ())], "reference": "dummy",
         "source": "id", "target": "id"}) | {"show_create": True}}


async def test_fk_output(
    base: DeclarativeBase, aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
    login: _Login
) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "test"
        id: Mapped[int] = mapped_column(primary_key=True)

    class TestModelParent(base):  # type: ignore[misc,valid-type]
        __tablename__ = "parent"
        id: Mapped[int] = mapped_column(primary_key=True)
        child_id: Mapped[int] = mapped_column(sa.ForeignKey(TestModel.id))

    app = web.Application()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    db = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)
    async with db.begin() as sess:
        child = TestModel()
        sess.add(child)
    async with db.begin() as sess:
        sess.add(TestModelParent(child_id=child.id))

    schema: aiohttp_admin.Schema = {
        "security": {
            "check_credentials": check_credentials,
            "secure": False
        },
        "resources": ({"model": SAResource(engine, TestModel)},
                      {"model": SAResource(engine, TestModelParent)})
    }
    app["admin"] = aiohttp_admin.setup(app, schema)

    admin_client = await aiohttp_client(app)
    assert admin_client.app
    h = await login(admin_client)

    url = app["admin"].router["parent_get_one"].url_for()
    async with admin_client.get(url, params={"id": 1}, headers=h) as resp:
        assert resp.status == 200
        # child_id must be converted to str ID.
        assert await resp.json() == {"data": {"id": "1", "child_id": "1"}}


def test_relationship(base: type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestMany(base):  # type: ignore[misc,valid-type]
        __tablename__ = "many"
        id: Mapped[int] = mapped_column(primary_key=True)
        foo: Mapped[int]
        ones: Mapped[list["TestOne"]] = relationship(back_populates="many")

    class TestOne(base):  # type: ignore[misc,valid-type]
        __tablename__ = "one"
        id: Mapped[int] = mapped_column(primary_key=True)
        many_id: Mapped[int] = mapped_column(sa.ForeignKey(TestMany.id))
        many: Mapped[TestMany] = relationship(back_populates="ones")

    r = SAResource(mock_engine, TestMany)
    assert r.name == "many"
    assert r.fields["ones"] == comp(
        "ReferenceManyField",
        {"children": (comp("Datagrid", {
            "rowClick": "show", "children": [comp("NumberField", {"source": "id"})],
            "bulkActionButtons": comp("BulkDeleteButton", {"mutationMode": "pessimistic"})}),),
         "label": "Ones", "reference": "one", "source": "id", "target": "many_id",
         "sortable": False})
    assert "ones" not in r.inputs

    r = SAResource(mock_engine, TestOne)
    assert r.name == "one"
    assert r.fields["many"] == comp(
        "ReferenceField",
        {"children": (comp("DatagridSingle", {
            "rowClick": "show", "children": [comp("NumberField", {"source": "foo"})]}),),
         "label": "Many", "reference": "many", "source": "many_id", "target": "id",
         "sortable": False, "link": "show"})
    assert "many" not in r.inputs


def test_relationship_onetoone(base: type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestA(base):  # type: ignore[misc,valid-type]
        __tablename__ = "test_a"
        id: Mapped[int] = mapped_column(primary_key=True)
        str: Mapped[str]
        other: Mapped["TestB"] = relationship(back_populates="linked")

    class TestB(base):  # type: ignore[misc,valid-type]
        __tablename__ = "test_b"
        id: Mapped[int] = mapped_column(primary_key=True)
        a_id: Mapped[int] = mapped_column(sa.ForeignKey(TestA.id))
        linked: Mapped[TestA] = relationship(back_populates="other")

    r = SAResource(mock_engine, TestA)
    assert r.name == "test_a"
    assert r.fields["other"] == comp(
        "ReferenceOneField",
        {"children": (comp("DatagridSingle", {
            "rowClick": "show", "children": [comp("NumberField", {"source": "id"})]}),),
         "label": "Other", "reference": "test_b", "source": "id", "target": "a_id",
         "sortable": False, "link": "show"})
    assert "other" not in r.inputs

    r = SAResource(mock_engine, TestB)
    assert r.name == "test_b"
    assert r.fields["linked"] == comp(
        "ReferenceField",
        {"children": (comp("DatagridSingle", {
            "rowClick": "show", "children": [comp("TextField", {"source": "str"})]}),),
         "label": "Linked", "reference": "test_a", "source": "a_id", "target": "id",
         "sortable": False, "link": "show"})
    assert "linked" not in r.inputs


def test_check_constraints(base: type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
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
        with_and: Mapped[int] = mapped_column()
        with_or: Mapped[int] = mapped_column()

        __table_args__ = (sa.CheckConstraint(gt > 3), sa.CheckConstraint(gte >= 3),
                          sa.CheckConstraint(lt < 3), sa.CheckConstraint(lte <= 3),
                          sa.CheckConstraint(sa.func.char_length(min_length) >= 5),
                          sa.CheckConstraint(sa.func.char_length(min_length_gt) > 5),
                          sa.CheckConstraint(sa.func.regexp(regex, r"abc.*")),
                          sa.CheckConstraint(sa.and_(with_and > 7, with_and < 12)),
                          sa.CheckConstraint(sa.or_(with_or > 7, with_or < 12)))

    r = SAResource(mock_engine, TestCC)

    f = r.inputs
    required = func("required", ())
    assert f["pk"]["props"]["validate"] == [required]
    assert f["default"]["props"]["validate"] == []
    assert f["server_default"]["props"]["validate"] == []
    assert f["nullable"]["props"]["validate"] == []
    assert f["not_nullable"]["props"]["validate"] == [required]
    assert f["max_length"]["props"]["validate"] == [required, func("maxLength", (16,))]
    assert f["gt"]["props"]["validate"] == [required, func("minValue", (4,))]
    assert f["gte"]["props"]["validate"] == [required, func("minValue", (3,))]
    assert f["lt"]["props"]["validate"] == [required, func("maxValue", (2,))]
    assert f["lte"]["props"]["validate"] == [func("maxValue", (3,))]
    assert f["min_length"]["props"]["validate"] == [required, func("minLength", (5,))]
    assert f["min_length_gt"]["props"]["validate"] == [required, func("minLength", (6,))]
    assert f["regex"]["props"]["validate"] == [required, func("regex", (regex("abc.*"),))]
    assert f["with_and"]["props"]["validate"] == [
        required, func("minValue", (8,)), func("maxValue", (11,))]
    assert f["with_or"]["props"]["validate"] == [required]


async def test_nonid_pk(base: type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "test"
        num: Mapped[int] = mapped_column(primary_key=True)
        other: Mapped[str] = mapped_column(sa.String(64))

    r = SAResource(mock_engine, TestModel)
    assert r.name == "test"
    assert r.primary_key == "num"
    assert r.fields == {
        "num": comp("NumberField", {"source": "num"}),
        "other": comp("TextField", {"source": "other", "fullWidth": True})
    }
    assert r.inputs == {
        "num": comp("NumberInput", {"source": "num", "validate": [func("required", ())]})
        | {"show_create": False},
        "other": comp("TextInput", {
            "fullWidth": True, "source": "other",
            "validate": [func("required", ()), func("maxLength", (64,))]})
        | {"show_create": True}
    }


async def test_id_nonpk(base: type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
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
        assert await resp.json() == {"data": [{"id": "8", "num": 8, "other": "bar"},
                                              {"id": "5", "num": 5, "other": "foo"}], "total": 2}

    url = app["admin"].router["test_get_one"].url_for()
    async with admin_client.get(url, params={"id": 8}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": "8", "num": 8, "other": "bar"}}

    url = app["admin"].router["test_get_many"].url_for()
    async with admin_client.get(url, params={"ids": '["5", "8"]'}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": "5", "num": 5, "other": "foo"},
                                              {"id": "8", "num": 8, "other": "bar"}]}

    url = app["admin"].router["test_create"].url_for()
    p = {"data": json.dumps({"num": 12, "other": "this"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": "12", "num": 12, "other": "this"}}

    url = app["admin"].router["test_update"].url_for()
    p1 = {"id": 5, "data": json.dumps({"id": 5, "other": "that"}), "previousData": "{}"}
    async with admin_client.put(url, params=p1, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": "5", "num": 5, "other": "that"}}


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
        assert await resp.json() == {"data": {"id": "1", "date": "2023-04-23",
                                              "time": "2023-01-02 03:04:00"}}

    url = app["admin"].router["test_create"].url_for()
    p = {"data": json.dumps({"date": "2024-05-09", "time": "2020-11-12 03:04:05"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": "2", "date": "2024-05-09",
                                              "time": "2020-11-12 03:04:05"}}


def test_permission_for(base: type[DeclarativeBase]) -> None:
    class M(base):  # type: ignore[misc,valid-type]
        __tablename__ = "test"
        id: Mapped[int] = mapped_column(primary_key=True)
        cat: Mapped[int]
        val: Mapped[str]

    t = M.__table__

    assert permission_for(M) == "admin.test.*"
    assert permission_for(M, "view") == "admin.test.view"
    assert permission_for(M, "add", negated=True) == "~admin.test.add"
    assert permission_for(M.cat, "edit") == "admin.test.cat.edit"
    assert permission_for(t.c["val"], "*", negated=True) == "~admin.test.val.*"
    assert permission_for(M, filters={M.cat: 5, M.val: "Foo"}) == 'admin.test.*|cat=5|val="Foo"'
    assert permission_for(
        t, "delete", filters={t.c["val"]: "bar"}) == 'admin.test.delete|val="bar"'
    assert permission_for(M.val, filters={M.id: (3, 4)}) == "admin.test.val.*|id=3|id=4"
    assert permission_for(
        M.cat, "edit", filters={M.cat: [1, 5]}) == "admin.test.cat.edit|cat=1|cat=5"

    with pytest.raises(ValueError, match="Can't use filters on negated"):
        permission_for(M, filters={M.id: 1}, negated=True)
    with pytest.raises(ValueError, match="foo"):
        permission_for(M, "foo")  # type: ignore[arg-type]

    class Wrong(base):  # type: ignore[misc,valid-type]
        __tablename__ = "wrong"
        id: Mapped[int] = mapped_column(primary_key=True)

    with pytest.raises(ValueError, match="not an attribute"):
        permission_for(M, filters={Wrong.id: 1})


async def test_record_type(
    base: DeclarativeBase, aiohttp_client: Callable[[web.Application], Awaitable[TestClient]],
    login: _Login
) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "test"
        id: Mapped[int] = mapped_column(primary_key=True)
        foo: Mapped[Optional[bool]]
        bar: Mapped[int]

    app = web.Application()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)

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

    url = app["admin"].router["test_create"].url_for()
    p = {"data": json.dumps({"foo": True, "bar": 5})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": "1", "foo": True, "bar": 5}}
    p = {"data": json.dumps({"foo": None, "bar": -1})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": "2", "foo": None, "bar": -1}}

    p = {"data": json.dumps({"foo": 5, "bar": "foo"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 400
        errors = await resp.json()
        assert any(e["loc"] == ["foo"] and e["type"] == "bool_parsing" for e in errors)
        assert any(e["loc"] == ["bar"] and e["type"] == "int_parsing" for e in errors)

    p = {"data": json.dumps({"foo": "foo", "bar": None})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 400
        errors = await resp.json()
        assert any(e["loc"] == ["foo"] and e["type"] == "bool_parsing" for e in errors)
        assert any(e["loc"] == ["bar"] and e["type"] == "int_type" for e in errors)
