from typing import Type

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from aiohttp_admin.backends.sqlalchemy import SAResource


def test_pk(base: Type[DeclarativeBase], mock_engine: AsyncEngine) -> None:
    class TestModel(base):  # type: ignore[misc,valid-type]
        __tablename__ = "dummy"
        id: Mapped[int] = mapped_column(primary_key=True)
        num: Mapped[str]

    r = SAResource(mock_engine, TestModel)
    assert r.name == "dummy"
    assert r.repr_field == "id"
    assert r.fields == {
        "id": {"type": "NumberField", "props": {}},
        "num": {"type": "TextField", "props": {}}
    }
    # Autoincremented PK should not be in create form
    assert r.inputs == {
        "id": {"type": "NumberInput", "show_create": False, "props": {}},
        "num": {"type": "TextInput", "show_create": True, "props": {}}
    }


def test_table(mock_engine: AsyncEngine) -> None:
    dummy_table = sa.Table("dummy", sa.MetaData(),
                           sa.Column("id", sa.Integer, primary_key=True),
                           sa.Column("num", sa.String(30)))

    r = SAResource(mock_engine, dummy_table)
    assert r.name == "dummy"
    assert r.repr_field == "id"
    assert r.fields == {
        "id": {"type": "NumberField", "props": {}},
        "num": {"type": "TextField", "props": {}}
    }
    # Autoincremented PK should not be in create form
    assert r.inputs == {
        "id": {"type": "NumberInput", "show_create": False, "props": {}},
        "num": {"type": "TextInput", "show_create": True, "props": {}}
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
    assert r.repr_field == "id"
    assert r.fields == {"id": {"type": "ReferenceField", "props": {"reference": "dummy"}}}
    # PK with FK constraint should be shown in create form.
    assert r.inputs == {"id": {
        "type": "ReferenceInput", "show_create": True, "props": {"reference": "dummy"}}}


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
