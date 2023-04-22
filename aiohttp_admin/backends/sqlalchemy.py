import asyncio
import logging
import operator
from typing import Any, Iterator, Type, Union

import sqlalchemy as sa
from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.roles import ExpressionElementRole

from .abc import (
    AbstractAdminResource, CreateParams, DeleteManyParams, DeleteParams, GetListParams,
    GetManyParams, GetOneParams, Record, UpdateManyParams, UpdateParams)

logger = logging.getLogger(__name__)

FIELD_TYPES = {
    sa.Integer: ("NumberField", "NumberInput"),
    sa.Text: ("TextField", "TextInput"),
    sa.Float: ("NumberField", "NumberInput"),
    sa.Date: ("DateField", "DateInput"),
    sa.DateTime: ("DateField", "DateInput"),
    sa.Boolean: ("BooleanField", "BooleanInput"),
    sa.String: ("TextField", "TextInput")
}


def create_filters(columns: sa.ColumnCollection[str, sa.Column[object]],
                   filters: dict[str, object]) -> Iterator[ExpressionElementRole[Any]]:
    return (columns[k].in_(v) if isinstance(v, list)
            else columns[k].ilike(f"%{v}%") if isinstance(v, str) else columns[k] == v
            for k, v in filters.items())


class SAResource(AbstractAdminResource):
    def __init__(self, db: AsyncEngine, model_or_table: Union[sa.Table, Type[DeclarativeBase]]):
        if isinstance(model_or_table, sa.Table):
            table = model_or_table
        else:
            if not isinstance(model_or_table.__table__, sa.Table):
                raise ValueError("Non-table mappings are not supported.")
            table = model_or_table.__table__

        self.name = table.name
        self.fields = {}
        self.inputs = {}
        for c in table.c.values():
            if c.foreign_keys:
                field = "ReferenceField"
                inp = "ReferenceInput"
                key = next(iter(c.foreign_keys))  # TODO: Test composite foreign keys.
                props: dict[str, object] = {"reference": key.column.table.name}
            else:
                field, inp = FIELD_TYPES.get(type(c.type), ("TextField", "TextInput"))
                props = {}
            self.fields[c.name] = {"type": field, "props": props}
            if c.computed is None:
                # TODO: Allow custom props (e.g. disabled, multiline, rows etc.)
                show = c is not table.autoincrement_column
                validators = self._get_validators(table, c)
                self.inputs[c.name] = {"type": inp, "props": props, "show_create": show,
                                       "validators": validators}

        if not isinstance(model_or_table, sa.Table):
            # Append fields to represent ORM relationships.
            mapper = sa.inspect(model_or_table)
            assert mapper is not None  # noqa: S101
            for name, relationship in mapper.relationships.items():
                if len(relationship.local_remote_pairs) > 1:
                    raise NotImplementedError("Composite foreign keys not supported yet.")
                pair = relationship.local_remote_pairs[0]
                children = {}
                for c in relationship.target.c.values():
                    if c is pair[1]:  # Skip the foreign key
                        continue
                    field, inp = FIELD_TYPES.get(type(c.type), ("TextField", "TextInput"))
                    children[c.name] = {"type": field, "props": {}}

                props = {"reference": relationship.entity.persist_selectable.name,
                         "label": name.title(), "children": children,
                         "source": pair[0].name, "target": pair[1].name}
                self.fields[name] = {"type": "ReferenceManyField", "props": props}

        self._db = db
        self._table = table

        pk = tuple(filter(lambda c: table.c[c].primary_key, self._table.c.keys()))
        if not pk:
            raise ValueError("No primary key found.")
        if len(pk) > 1:
            # TODO: Test composite primary key
            raise NotImplementedError("Composite keys not supported yet.")
        self.primary_key = pk[0]

        super().__init__()

    async def get_list(self, params: GetListParams) -> tuple[list[Record], int]:
        per_page = params["pagination"]["perPage"]
        offset = (params["pagination"]["page"] - 1) * per_page

        filters = params["filter"]
        async with self._db.connect() as conn:
            query = sa.select(self._table)
            if filters:
                query = query.where(*create_filters(self._table.c, filters))

            count_t = conn.scalar(sa.select(sa.func.count()).select_from(query.subquery()))

            sort_dir = sa.asc if params["sort"]["order"] == "ASC" else sa.desc
            order_by: sa.UnaryExpression[object] = sort_dir(params["sort"]["field"])
            stmt = query.offset(offset).limit(per_page).order_by(order_by)
            result, count = await asyncio.gather(conn.execute(stmt), count_t)
            entities = [r._asdict() for r in result]

        return entities, count

    async def get_one(self, params: GetOneParams) -> Record:
        async with self._db.connect() as conn:
            stmt = sa.select(self._table).where(self._table.c[self.primary_key] == params["id"])
            result = await conn.execute(stmt)
            try:
                return result.one()._asdict()
            except sa.exc.NoResultFound:
                logger.warning("No result found (%s)", params["id"], exc_info=True)
                raise web.HTTPNotFound()

    async def get_many(self, params: GetManyParams) -> list[Record]:
        async with self._db.connect() as conn:
            stmt = sa.select(self._table).where(self._table.c[self.primary_key].in_(params["ids"]))
            result = await conn.execute(stmt)
            records = [r._asdict() for r in result]
        if records:
            return records
        raise web.HTTPNotFound()

    async def create(self, params: CreateParams) -> Record:
        async with self._db.begin() as conn:
            stmt = sa.insert(self._table).values(params["data"]).returning(*self._table.c)
            try:
                row = await conn.execute(stmt)
            except sa.exc.IntegrityError:
                logger.warning("IntegrityError (%s)", params["data"], exc_info=True)
                raise web.HTTPBadRequest(reason="Integrity error (element already exists?)")
            return row.one()._asdict()

    async def update(self, params: UpdateParams) -> Record:
        async with self._db.begin() as conn:
            stmt = sa.update(self._table).where(self._table.c[self.primary_key] == params["id"])
            stmt = stmt.values(params["data"]).returning(*self._table.c)
            try:
                row = await conn.execute(stmt)
            except sa.exc.CompileError as e:
                logger.warning("CompileError (%s)", params["id"], exc_info=True)
                raise web.HTTPBadRequest(reason=str(e))
            try:
                return row.one()._asdict()
            except sa.exc.NoResultFound:
                logger.warning("No result found (%s)", params["id"], exc_info=True)
                raise web.HTTPNotFound()

    async def update_many(self, params: UpdateManyParams) -> list[Union[str, int]]:
        async with self._db.begin() as conn:
            stmt = sa.update(self._table).where(self._table.c[self.primary_key].in_(params["ids"]))
            stmt = stmt.values(params["data"]).returning(self._table.c[self.primary_key])
            try:
                r = await conn.scalars(stmt)
            except sa.exc.CompileError as e:
                logger.warning("CompileError (%s)", params["ids"], exc_info=True)
                raise web.HTTPBadRequest(reason=str(e))
            # The security check has already called get_many(), so we can be sure
            # there will be results here.
            return list(r)

    async def delete(self, params: DeleteParams) -> Record:
        async with self._db.begin() as conn:
            stmt = sa.delete(self._table).where(self._table.c[self.primary_key] == params["id"])
            row = await conn.execute(stmt.returning(*self._table.c))
            try:
                return row.one()._asdict()
            except sa.exc.NoResultFound:
                logger.warning("No result found (%s)", params["id"], exc_info=True)
                raise web.HTTPNotFound()

    async def delete_many(self, params: DeleteManyParams) -> list[Union[str, int]]:
        async with self._db.begin() as conn:
            stmt = sa.delete(self._table).where(self._table.c[self.primary_key].in_(params["ids"]))
            r = await conn.scalars(stmt.returning(self._table.c[self.primary_key]))
            ids = list(r)
        if ids:
            return ids
        raise web.HTTPNotFound()

    def _get_validators(self, table: sa.Table, c: sa.Column[object]) -> list[tuple[Union[str, int], ...]]:
        validators: list[tuple[Union[str, int], ...]] = []
        if c.default is None and c.server_default is None and not c.nullable:
            validators.append(("required",))
        max_length = getattr(c.type, "length", None)
        if max_length:
            validators.append(("maxLength", max_length))

        for constr in table.constraints:
            if not isinstance(constr, sa.CheckConstraint):
                continue
            if isinstance(constr.sqltext, sa.BinaryExpression):
                if constr.sqltext.left.expression is c:
                    if not isinstance(constr.sqltext.right, sa.BindParameter):
                        continue
                    if constr.sqltext.right.value is None:
                        continue
                    if constr.sqltext.operator is operator.ge:
                        validators.append(("minValue", constr.sqltext.right.value))
                    elif constr.sqltext.operator is operator.gt:
                        validators.append(("minValue", constr.sqltext.right.value + 1))
                    elif constr.sqltext.operator is operator.le:
                        validators.append(("maxValue", constr.sqltext.right.value))
                    elif constr.sqltext.operator is operator.lt:
                        validators.append(("maxValue", constr.sqltext.right.value - 1))
                elif isinstance(constr.sqltext.left, sa.Function):
                    if constr.sqltext.left.name == "char_length":
                        if next(iter(constr.sqltext.left.clauses)) is not c:
                            continue
                        if not isinstance(constr.sqltext.right, sa.BindParameter):
                            continue
                        if constr.sqltext.right.value is None:
                            continue
                        if constr.sqltext.operator is operator.ge:
                            validators.append(("minLength", constr.sqltext.right.value))
                        elif constr.sqltext.operator is operator.gt:
                            validators.append(("minLength", constr.sqltext.right.value + 1))
            elif isinstance(constr.sqltext, sa.Function):
                if constr.sqltext.name in ("regexp", "regexp_like"):
                    clauses = tuple(constr.sqltext.clauses)
                    if clauses[0] is not c or not isinstance(clauses[1], sa.BindParameter):
                        continue
                    if clauses[1].value is None:
                        continue
                    validators.append(("regex", clauses[1].value))

        return validators
