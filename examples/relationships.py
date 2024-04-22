"""Example that demonstrates use of various foreign key relationships.

An example of each SQLAlchemy relationship is included.
However, the many to many relationship requires the react-admin enterprise-edition
(not currently supported by aiohttp-admin).
https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html

When running this file, admin will be accessible at /admin.
"""

import sqlalchemy as sa
from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import aiohttp_admin
from aiohttp_admin.backends.sqlalchemy import SAResource


class Base(DeclarativeBase):
    """Base model."""


class OneToManyParent(Base):
    __tablename__ = "onetomany_parent"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[int]
    children: Mapped[list["OneToManyChild"]] = relationship(back_populates="parent")


class OneToManyChild(Base):
    __tablename__ = "onetomany_child"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[int]
    parent_id: Mapped[int] = mapped_column(sa.ForeignKey(OneToManyParent.id))
    parent: Mapped[OneToManyParent] = relationship(back_populates="children")


class ManyToOneParent(Base):
    __tablename__ = "manytoone_parent"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[int]
    child_id: Mapped[int | None] = mapped_column(sa.ForeignKey("manytoone_child.id"))
    child: Mapped["ManyToOneChild | None"] = relationship(back_populates="parents")


class ManyToOneChild(Base):
    __tablename__ = "manytoone_child"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[int]
    parents: Mapped[list[ManyToOneParent]] = relationship(back_populates="child")


class OneToOneParent(Base):
    __tablename__ = "onetoone_parent"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[int]
    child: Mapped["OneToOneChild"] = relationship(back_populates="parent")


class OneToOneChild(Base):
    __tablename__ = "onetoone_child"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[int]
    parent_id: Mapped[int] = mapped_column(sa.ForeignKey(OneToOneParent.id))
    parent: Mapped[OneToOneParent] = relationship(back_populates="child")


association_table = sa.Table(
    "association_table",
    Base.metadata,
    sa.Column("left_id", sa.ForeignKey("manytomany_left.id"), primary_key=True),
    sa.Column("right_id", sa.ForeignKey("manytomany_right.id"), primary_key=True),
)


class ManyToManyParent(Base):
    __tablename__ = "manytomany_left"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[int]
    children: Mapped[list["ManyToManyChild"]] = relationship(secondary=association_table,
                                                             back_populates="parents")


class ManyToManyChild(Base):
    __tablename__ = "manytomany_right"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[int]
    parents: Mapped[list[ManyToManyParent]] = relationship(secondary=association_table,
                                                           back_populates="children")


class CompositeForeignKeyChild(Base):
    __tablename__ = "composite_foreign_key_child"

    num: Mapped[int] = mapped_column(primary_key=True)
    ref_num: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(sa.String(64))

    parents: Mapped[list["CompositeForeignKeyParent"]] = relationship(back_populates="child")


class CompositeForeignKeyParent(Base):
    __tablename__ = "composite_foreign_key_parent"

    item_id: Mapped[int] = mapped_column(primary_key=True)
    item_name: Mapped[str] = mapped_column(sa.String(64))
    child_id: Mapped[int]
    ref_num: Mapped[int]

    child: Mapped[CompositeForeignKeyChild] = relationship(back_populates="parents")

    @sa.orm.declared_attr.directive
    @classmethod
    def __table_args__(cls) -> tuple[sa.schema.SchemaItem, ...]:
        return (sa.ForeignKeyConstraint(
            ["child_id", "ref_num"],
            ["composite_foreign_key_child.num", "composite_foreign_key_child.ref_num"]
        ),)


async def check_credentials(username: str, password: str) -> bool:
    return username == "admin" and password == "admin"


async def create_app() -> web.Application:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session = async_sessionmaker(engine, expire_on_commit=False)

    # Create some sample data
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session.begin() as sess:
        sess.add(OneToManyParent(name="Foo", value=1))
        onetomany_1 = OneToManyParent(name="Bar", value=2)
        sess.add(onetomany_1)
        manytoone_1 = ManyToOneChild(name="Child Foo", value=4)
        sess.add(manytoone_1)
        onetoone_1 = OneToOneParent(name="Foo", value=3)
        sess.add(onetoone_1)
        onetoone_2 = OneToOneParent(name="Bar", value=5)
        sess.add(onetoone_2)
        manytomany_p1 = ManyToManyParent(name="Foo", value=2)
        manytomany_p2 = ManyToManyParent(name="Bar", value=3)
        manytomany_c1 = ManyToManyChild(name="Foo Child", value=5)
        manytomany_c2 = ManyToManyChild(name="Bar Child", value=6)
        manytomany_c3 = ManyToManyChild(name="Baz Child", value=7)
        manytomany_p1.children.append(manytomany_c1)
        manytomany_p1.children.append(manytomany_c2)
        manytomany_p2.children.append(manytomany_c1)
        manytomany_p2.children.append(manytomany_c2)
        manytomany_p2.children.append(manytomany_c3)
        sess.add(manytomany_p1)
        sess.add(manytomany_p2)
        sess.add(manytomany_c1)
        sess.add(manytomany_c2)
        composite_child_1 = CompositeForeignKeyChild(num=0, ref_num=0, description="A")
        composite_child_2 = CompositeForeignKeyChild(num=0, ref_num=1, description="B")
        composite_child_3 = CompositeForeignKeyChild(num=1, ref_num=0, description="C")
        sess.add(composite_child_1)
        sess.add(composite_child_2)
        sess.add(composite_child_3)
        sess.add(CompositeForeignKeyParent(item_name="Foo", child_id=0, ref_num=1))
        sess.add(CompositeForeignKeyParent(item_name="Bar", child_id=1, ref_num=0))
    async with session.begin() as sess:
        sess.add(OneToManyChild(name="Child Foo", value=1, parent_id=onetomany_1.id))
        sess.add(OneToManyChild(name="Child Bar", value=5, parent_id=onetomany_1.id))
        sess.add(ManyToOneParent(name="Foo", value=5, child_id=manytoone_1.id))
        sess.add(ManyToOneParent(name="Bar", value=3))
        sess.add(OneToOneChild(name="Child Foo", value=0, parent_id=onetoone_2.id))
        sess.add(OneToOneChild(name="Child Bar", value=2, parent_id=onetoone_1.id))

    app = web.Application()

    # This is the setup required for aiohttp-admin.
    schema: aiohttp_admin.Schema = {
        "security": {
            "check_credentials": check_credentials,
            "secure": False
        },
        "resources": (
            {"model": SAResource(engine, OneToManyParent), "repr": aiohttp_admin.data("name")},
            {"model": SAResource(engine, OneToManyChild)},
            {"model": SAResource(engine, ManyToOneParent), "repr": aiohttp_admin.data("name")},
            {"model": SAResource(engine, ManyToOneChild)},
            {"model": SAResource(engine, OneToOneParent), "repr": aiohttp_admin.data("name")},
            {"model": SAResource(engine, OneToOneChild)},
            {"model": SAResource(engine, ManyToManyParent)},
            {"model": SAResource(engine, ManyToManyChild)},
            {"model": SAResource(engine, CompositeForeignKeyChild),
             "repr": aiohttp_admin.data("description")},
            {"model": SAResource(engine, CompositeForeignKeyParent)}
        )
    }
    aiohttp_admin.setup(app, schema)

    return app

if __name__ == "__main__":
    web.run_app(create_app())
