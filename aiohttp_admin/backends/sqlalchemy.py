import asyncio
import json
import logging
import operator
import sys
from collections.abc import Callable, Coroutine, Iterator, Sequence
from types import MappingProxyType as MPT
from typing import Any, Literal, Optional, TypeVar, Union

import sqlalchemy as sa
from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import DeclarativeBase, QueryableAttribute
from sqlalchemy.sql.roles import ExpressionElementRole

from .abc import (
    AbstractAdminResource, CreateParams, DeleteManyParams, DeleteParams, GetListParams,
    GetManyParams, GetOneParams, Record, UpdateManyParams, UpdateParams)

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec

_P = ParamSpec("_P")
_T = TypeVar("_T")
_FValues = Union[bool, int, str]
_Filters = dict[Union[sa.Column[object], QueryableAttribute[Any]],
                Union[_FValues, Sequence[_FValues]]]

logger = logging.getLogger(__name__)

FIELD_TYPES: MPT[type[sa.types.TypeEngine[Any]], tuple[str, str, MPT[str, bool]]] = MPT({
    sa.Boolean: ("BooleanField", "BooleanInput", MPT({})),
    sa.Date: ("DateField", "DateInput", MPT({"showDate": True, "showTime": False})),
    sa.DateTime: ("DateField", "DateTimeInput", MPT({"showDate": True, "showTime": True})),
    sa.Enum: ("SelectField", "SelectInput", MPT({})),
    sa.Integer: ("NumberField", "NumberInput", MPT({})),
    sa.Numeric: ("NumberField", "NumberInput", MPT({})),
    sa.String: ("TextField", "TextInput", MPT({})),
    sa.Time: ("TimeField", "TimeInput", MPT({})),
    sa.Uuid: ("TextField", "TextInput", MPT({})),  # TODO: validators
    # TODO: Set fields for below types.
    # sa.sql.sqltypes._AbstractInterval: (),
    # sa.types._Binary: (),
    # sa.types.PickleType: (),

    # sa.ARRAY: (),
    # sa.JSON: (),

    # sa.dialects.postgresql.AbstractRange: (),
    # sa.dialects.postgresql.BIT: (),
    # sa.dialects.postgresql.CIDR: (),
    # sa.dialects.postgresql.HSTORE: (),
    # sa.dialects.postgresql.INET: (),
    # sa.dialects.postgresql.MACADDR: (),
    # sa.dialects.postgresql.MACADDR8: (),
    # sa.dialects.postgresql.MONEY: (),
    # sa.dialects.postgresql.OID: (),
    # sa.dialects.postgresql.REGCONFIG: (),
    # sa.dialects.postgresql.REGCLASS: (),
    # sa.dialects.postgresql.TSQUERY: (),
    # sa.dialects.postgresql.TSVECTOR: (),
    # sa.dialects.mysql.BIT: (),
    # sa.dialects.mysql.YEAR: (),
    # sa.dialects.oracle.ROWID: (),
    # sa.dialects.mssql.MONEY: (),
    # sa.dialects.mssql.SMALLMONEY: (),
    # sa.dialects.mssql.SQL_VARIANT: (),
})


def get_components(t: sa.types.TypeEngine[object]) -> tuple[str, str, dict[str, bool]]:
    for key, (field, inp, props) in FIELD_TYPES.items():
        if isinstance(t, key):
            return (field, inp, props.copy())

    return ("TextField", "TextInput", {})


def handle_errors(
    f: Callable[_P, Coroutine[None, None, _T]]
) -> Callable[_P, Coroutine[None, None, _T]]:
    async def inner(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        try:
            return await f(*args, **kwargs)
        except sa.exc.IntegrityError as e:
            raise web.HTTPBadRequest(reason=e.args[0])
        except sa.exc.NoResultFound:
            logger.warning("No result found (%s)", args, exc_info=True)
            raise web.HTTPNotFound()
        except sa.exc.CompileError as e:
            logger.warning("CompileError (%s)", args, exc_info=True)
            raise web.HTTPBadRequest(reason=str(e))
    return inner


def permission_for(sa_obj: Union[sa.Table, type[DeclarativeBase],
                                 sa.Column[object], QueryableAttribute[Any]],
                   perm_type: Literal["view", "edit", "add", "delete", "*"] = "*",
                   *, filters: Optional[_Filters] = None, negated: bool = False) -> str:
    """Returns a permission string for the given sa_obj.

    Args:
        sa_obj: A SQLAlchemy object to grant permission to (table/model/column/attribute).
        perm_type: The type of permission to grant acces to.
        filters: Filters to restrict the permisson to (can't be used with negated).
                 e.g. {User.type: "admin", User.active: True} only permits access if
                      `User.type == "admin" and User.active`.
                      {Post.type: ("news", "sports")} only permits access if
                      `Post.type in ("news", "sports")`.
        negated: True if result should restrict access from sa_obj.
    """
    if filters and negated:
        raise ValueError("Can't use filters on negated permissions.")
    if perm_type not in {"view", "edit", "add", "delete", "*"}:
        raise ValueError(f"Invalid perm_type: '{perm_type}'")

    field = None
    if isinstance(sa_obj, sa.Table):
        table = sa_obj
    elif isinstance(sa_obj, (sa.Column, QueryableAttribute)):
        table = sa_obj.table
        field = sa_obj.name
    else:
        if not isinstance(sa_obj.__table__, sa.Table):
            raise ValueError("Non-table mappings are not supported.")
        table = sa_obj.__table__
    p = "{}admin.{}".format("~" if negated else "", table.name)

    if field:
        p = f"{p}.{field}"

    p = f"{p}.{perm_type}"

    if filters:
        for col, value in filters.items():
            if col.table is not table:
                raise ValueError("Filter key not an attribute/column of sa_obj.")
            # Sequences should be treated as multiple filter values for that key.
            if not isinstance(value, Sequence) or isinstance(value, str):
                value = (value,)
            for v in value:
                v = json.dumps(v)
                p += f"|{col.name}={v}"

    return p


def create_filters(columns: sa.ColumnCollection[str, sa.Column[object]],
                   filters: dict[str, object]) -> Iterator[ExpressionElementRole[Any]]:
    return (columns[k].in_(v) if isinstance(v, list)
            else columns[k].ilike(f"%{v}%") if isinstance(v, str) else columns[k] == v
            for k, v in filters.items())


class SAResource(AbstractAdminResource):
    def __init__(self, db: AsyncEngine, model_or_table: Union[sa.Table, type[DeclarativeBase]]):
        if isinstance(model_or_table, sa.Table):
            table = model_or_table
        else:
            if not isinstance(model_or_table.__table__, sa.Table):
                raise ValueError("Non-table mappings are not supported.")
            table = model_or_table.__table__

        self.name = table.name
        self.fields = {}
        self.inputs = {}
        self.omit_fields = set()
        for c in table.c.values():
            if c.foreign_keys:
                field = "ReferenceField"
                inp = "ReferenceInput"
                key = next(iter(c.foreign_keys))  # TODO: Test composite foreign keys.
                props: dict[str, Any] = {"reference": key.column.table.name,
                                         "source": c.name, "target": key.column.name}
            else:
                field, inp, props = get_components(c.type)

            if isinstance(c.type, sa.Enum):
                props["choices"] = tuple({"id": e.value, "name": e.name}
                                         for e in c.type.python_type)

            if isinstance(c.default, sa.ColumnDefault):
                props["placeholder"] = c.default.arg

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
                # https://github.com/sqlalchemy/sqlalchemy/discussions/10161#discussioncomment-6583442
                assert relationship.local_remote_pairs  # noqa: S101
                if len(relationship.local_remote_pairs) > 1:
                    raise NotImplementedError("Composite foreign keys not supported yet.")
                if not isinstance(relationship.entity.persist_selectable, sa.Table):
                    continue
                local, remote = relationship.local_remote_pairs[0]

                props = {"reference": relationship.entity.persist_selectable.name,
                         "label": name.title(), "source": local.name,
                         "target": remote.name, "sortable": False}
                if local.foreign_keys:
                    t = "ReferenceField"
                    props["link"] = "show"
                elif relationship.uselist:
                    t = "ReferenceManyField"
                else:
                    t = "ReferenceOneField"
                    props["link"] = "show"

                children = {}
                for kc in relationship.target.c.values():
                    if kc is remote:  # Skip the foreign key
                        continue
                    field, inp, c_props = get_components(kc.type)
                    children[kc.name] = {"type": field, "props": c_props}
                container = "Datagrid" if t == "ReferenceManyField" else "DatagridSingle"
                props["children"] = {"_": {"type": container, "props": {
                    "children": children, "rowClick": "show"}}}

                self.fields[name] = {"type": t, "props": props}
                self.omit_fields.add(name)

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

    @handle_errors
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

    @handle_errors
    async def get_one(self, params: GetOneParams) -> Record:
        async with self._db.connect() as conn:
            stmt = sa.select(self._table).where(self._table.c[self.primary_key] == params["id"])
            result = await conn.execute(stmt)
            return result.one()._asdict()

    @handle_errors
    async def get_many(self, params: GetManyParams) -> list[Record]:
        async with self._db.connect() as conn:
            stmt = sa.select(self._table).where(self._table.c[self.primary_key].in_(params["ids"]))
            result = await conn.execute(stmt)
            return [r._asdict() for r in result]

    @handle_errors
    async def create(self, params: CreateParams) -> Record:
        async with self._db.begin() as conn:
            stmt = sa.insert(self._table).values(params["data"]).returning(*self._table.c)
            try:
                row = await conn.execute(stmt)
            except sa.exc.IntegrityError:
                logger.warning("IntegrityError (%s)", params["data"], exc_info=True)
                raise web.HTTPBadRequest(reason="Integrity error (element already exists?)")
            return row.one()._asdict()

    @handle_errors
    async def update(self, params: UpdateParams) -> Record:
        async with self._db.begin() as conn:
            stmt = sa.update(self._table).where(self._table.c[self.primary_key] == params["id"])
            stmt = stmt.values(params["data"]).returning(*self._table.c)
            row = await conn.execute(stmt)
            return row.one()._asdict()

    @handle_errors
    async def update_many(self, params: UpdateManyParams) -> list[Union[str, int]]:
        async with self._db.begin() as conn:
            stmt = sa.update(self._table).where(self._table.c[self.primary_key].in_(params["ids"]))
            stmt = stmt.values(params["data"]).returning(self._table.c[self.primary_key])
            return list(await conn.scalars(stmt))

    @handle_errors
    async def delete(self, params: DeleteParams) -> Record:
        async with self._db.begin() as conn:
            stmt = sa.delete(self._table).where(self._table.c[self.primary_key] == params["id"])
            row = await conn.execute(stmt.returning(*self._table.c))
            return row.one()._asdict()

    @handle_errors
    async def delete_many(self, params: DeleteManyParams) -> list[Union[str, int]]:
        async with self._db.begin() as conn:
            stmt = sa.delete(self._table).where(self._table.c[self.primary_key].in_(params["ids"]))
            r = await conn.scalars(stmt.returning(self._table.c[self.primary_key]))
            return list(r)

    def _get_validators(
        self, table: sa.Table, c: sa.Column[object]
    ) -> list[tuple[Union[str, int], ...]]:
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
                left = constr.sqltext.left
                right = constr.sqltext.right
                op = constr.sqltext.operator
                if left.expression is c:
                    if not isinstance(right, sa.BindParameter) or right.value is None:
                        continue
                    if op is operator.ge:  # type: ignore[comparison-overlap]
                        validators.append(("minValue", right.value))
                    elif op is operator.gt:  # type: ignore[comparison-overlap]
                        validators.append(("minValue", right.value + 1))
                    elif op is operator.le:  # type: ignore[comparison-overlap]
                        validators.append(("maxValue", right.value))
                    elif op is operator.lt:  # type: ignore[comparison-overlap]
                        validators.append(("maxValue", right.value - 1))
                elif isinstance(left, sa.Function):
                    if left.name == "char_length":
                        if next(iter(left.clauses)) is not c:
                            continue
                        if not isinstance(right, sa.BindParameter) or right.value is None:
                            continue
                        if op is operator.ge:  # type: ignore[comparison-overlap]
                            validators.append(("minLength", right.value))
                        elif op is operator.gt:  # type: ignore[comparison-overlap]
                            validators.append(("minLength", right.value + 1))
            elif isinstance(constr.sqltext, sa.Function):
                if constr.sqltext.name in ("regexp", "regexp_like"):
                    clauses = tuple(constr.sqltext.clauses)
                    if clauses[0] is not c or not isinstance(clauses[1], sa.BindParameter):
                        continue
                    if clauses[1].value is None:
                        continue
                    validators.append(("regex", clauses[1].value))

        return validators
