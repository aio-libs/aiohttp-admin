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

from .abc import AbstractAdminResource, GetListParams, Meta, Record
from ..types import FunctionState, comp, func, regex

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


# ID is based on PK, which we can't infer from types, so must use Any here.
class SAResource(AbstractAdminResource[Any]):
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
        self._foreign_rows = set()
        record_type = {}
        for c in table.c.values():
            if c.foreign_keys:
                field = "ReferenceField"
                inp = "ReferenceInput"
                key = next(iter(c.foreign_keys))  # TODO: Test composite foreign keys.
                self._foreign_rows.add(c.name)
                props: dict[str, Any] = {"reference": key.column.table.name,
                                         "target": key.column.name}
            else:
                field, inp, props = get_components(c.type)

            if inp == "BooleanInput" and c.nullable:
                inp = "NullableBooleanInput"

            props["source"] = c.name
            if isinstance(c.type, sa.Enum):
                props["choices"] = tuple({"id": e.value, "name": e.name}
                                         for e in c.type.python_type)

            length = getattr(c.type, "length", 0)
            if length is None or length > 31:
                props["fullWidth"] = True
                if length is None or length > 127:
                    props["multiline"] = True

            if isinstance(c.default, sa.ColumnDefault):
                props["placeholder"] = c.default.arg

            if c.comment:
                props["helperText"] = c.comment

            self.fields[c.name] = comp(field, props)
            if c.computed is None:
                # TODO: Allow custom props (e.g. disabled, multiline, rows etc.)
                props = props.copy()
                show = c is not table.autoincrement_column
                props["validate"] = self._get_validators(table, c)
                if inp == "NumberInput":
                    for v in props["validate"]:
                        if v["name"] == "minValue":
                            props["min"] = v["args"][0]
                        elif v["name"] == "maxValue":
                            props["max"] = v["args"][0]
                self.inputs[c.name] = comp(inp, props)  # type: ignore[assignment]
                self.inputs[c.name]["show_create"] = show
                field_type: Any = c.type.python_type
                if c.nullable:
                    field_type = Optional[field_type]
                record_type[c.name] = field_type

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

                children = []
                for kc in relationship.target.c.values():
                    if kc is remote:  # Skip the foreign key
                        continue
                    field, inp, c_props = get_components(kc.type)
                    c_props["source"] = kc.name
                    children.append(comp(field, c_props))
                container = "Datagrid" if t == "ReferenceManyField" else "DatagridSingle"
                datagrid = comp(container, {"children": children, "rowClick": "show"})
                if t == "ReferenceManyField":
                    datagrid["props"]["bulkActionButtons"] = comp(
                        "BulkDeleteButton", {"mutationMode": "pessimistic"})
                props["children"] = (datagrid,)

                self.fields[name] = comp(t, props)
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
        self._id_type = table.c[pk[0]].type.python_type

        super().__init__(record_type)

    @handle_errors
    async def get_list(self, params: GetListParams) -> tuple[list[Record], int]:
        per_page = params["pagination"]["perPage"]
        offset = (params["pagination"]["page"] - 1) * per_page

        filters = params["filter"]
        query = sa.select(self._table)
        if filters:
            query = query.where(*create_filters(self._table.c, filters))

        async def get_count() -> int:
            async with self._db.connect() as conn:
                count = await conn.scalar(sa.select(sa.func.count()).select_from(query.subquery()))
                if count is None:
                    raise RuntimeError("Failed to get count.")
                return count

        async def get_entities() -> list[Record]:
            async with self._db.connect() as conn:
                sort_dir = sa.asc if params["sort"]["order"] == "ASC" else sa.desc
                order_by: sa.UnaryExpression[object] = sort_dir(params["sort"]["field"])
                stmt = query.offset(offset).limit(per_page).order_by(order_by)
                return [r._asdict() for r in await conn.execute(stmt)]

        return await asyncio.gather(get_entities(), get_count())

    @handle_errors
    async def get_one(self, record_id: Any, meta: Meta) -> Record:
        async with self._db.connect() as conn:
            stmt = sa.select(self._table).where(self._table.c[self.primary_key] == record_id)
            result = await conn.execute(stmt)
            return result.one()._asdict()

    @handle_errors
    async def get_many(self, record_ids: Sequence[Any], meta: Meta) -> list[Record]:
        async with self._db.connect() as conn:
            stmt = sa.select(self._table).where(self._table.c[self.primary_key].in_(record_ids))
            result = await conn.execute(stmt)
            return [r._asdict() for r in result]

    @handle_errors
    async def create(self, data: Record, meta: Meta) -> Record:
        async with self._db.begin() as conn:
            stmt = sa.insert(self._table).values(data).returning(*self._table.c)
            try:
                row = await conn.execute(stmt)
            except sa.exc.IntegrityError:
                logger.warning("IntegrityError (%s)", data, exc_info=True)
                raise web.HTTPBadRequest(reason="Integrity error (element already exists?)")
            return row.one()._asdict()

    @handle_errors
    async def update(self, record_id: Any, data: Record, previous_data: Record,
                     meta: Meta) -> Record:
        async with self._db.begin() as conn:
            stmt = sa.update(self._table).where(self._table.c[self.primary_key] == record_id)
            stmt = stmt.values(data).returning(*self._table.c)
            row = await conn.execute(stmt)
            return row.one()._asdict()

    @handle_errors
    async def update_many(self, record_ids: Sequence[Any], data: Record, meta: Meta) -> list[Any]:
        async with self._db.begin() as conn:
            stmt = sa.update(self._table).where(self._table.c[self.primary_key].in_(record_ids))
            stmt = stmt.values(data).returning(self._table.c[self.primary_key])
            return list(await conn.scalars(stmt))

    @handle_errors
    async def delete(self, record_id: Any, previous_data: Record, meta: Meta) -> Record:
        async with self._db.begin() as conn:
            stmt = sa.delete(self._table).where(self._table.c[self.primary_key] == record_id)
            row = await conn.execute(stmt.returning(*self._table.c))
            return row.one()._asdict()

    @handle_errors
    async def delete_many(self, record_ids: Sequence[Any], meta: Meta) -> list[Any]:
        async with self._db.begin() as conn:
            stmt = sa.delete(self._table).where(self._table.c[self.primary_key].in_(record_ids))
            r = await conn.scalars(stmt.returning(self._table.c[self.primary_key]))
            return list(r)

    def _get_validators(self, table: sa.Table, c: sa.Column[object]) -> list[FunctionState]:
        validators: list[FunctionState] = []
        if c.default is None and c.server_default is None and not c.nullable:
            validators.append(func("required", ()))
        max_length = getattr(c.type, "length", None)
        if max_length:
            validators.append(func("maxLength", (max_length,)))

        for constr in table.constraints:
            if not isinstance(constr, sa.CheckConstraint):
                continue

            if isinstance(constr.sqltext, sa.BooleanClauseList):
                if constr.sqltext.operator is not operator.and_:  # type: ignore[comparison-overlap]
                    continue
                exprs = constr.sqltext.clauses
            else:
                exprs = (constr.sqltext,)

            for expr in exprs:
                if isinstance(expr, sa.BinaryExpression):
                    left = expr.left
                    right = expr.right
                    op = expr.operator
                    if left.expression is c:
                        if not isinstance(right, sa.BindParameter) or right.value is None:
                            continue
                        if op is operator.ge:  # type: ignore[comparison-overlap]
                            validators.append(func("minValue", (right.value,)))
                        elif op is operator.gt:  # type: ignore[comparison-overlap]
                            validators.append(func("minValue", (right.value + 1,)))
                        elif op is operator.le:  # type: ignore[comparison-overlap]
                            validators.append(func("maxValue", (right.value,)))
                        elif op is operator.lt:  # type: ignore[comparison-overlap]
                            validators.append(func("maxValue", (right.value - 1,)))
                    elif isinstance(left, sa.Function):
                        if left.name == "char_length":
                            if next(iter(left.clauses)) is not c:
                                continue
                            if not isinstance(right, sa.BindParameter) or right.value is None:
                                continue
                            if op is operator.ge:  # type: ignore[comparison-overlap]
                                validators.append(func("minLength", (right.value,)))
                            elif op is operator.gt:  # type: ignore[comparison-overlap]
                                validators.append(func("minLength", (right.value + 1,)))
                elif isinstance(expr, sa.Function):
                    if expr.name in ("regexp", "regexp_like"):
                        clauses = tuple(expr.clauses)
                        if clauses[0] is not c or not isinstance(clauses[1], sa.BindParameter):
                            continue
                        if clauses[1].value is None:
                            continue
                        validators.append(func("regex", (regex(clauses[1].value),)))

        return validators
