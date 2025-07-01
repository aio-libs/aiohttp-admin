import asyncio
import json
import logging
import operator
import sys
from collections.abc import Callable, Coroutine, Iterator, Sequence
from types import MappingProxyType as MPT
from typing import Any, Literal, Optional, TypeVar, Union, cast

import sqlalchemy as sa
from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import (DeclarativeBase, DeclarativeBaseNoMeta, Mapper,
                            QueryableAttribute, selectinload)

from .abc import AbstractAdminResource, GetListParams, GetManyRefParams, Meta, Record
from ..types import FunctionState, comp, data, fk, func, regex

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec

_P = ParamSpec("_P")
_T = TypeVar("_T")
_FValues = Union[bool, int, str]
_Filters = dict[Union[sa.Column[object], QueryableAttribute[Any]],
                Union[_FValues, Sequence[_FValues]]]
_ModelOrTable = Union[sa.Table, type[DeclarativeBase], type[DeclarativeBaseNoMeta]]
_SABoolExpression = sa.sql.roles.ExpressionElementRole[bool]
# _RelationshipAttr = InstrumentedAttribute[Union[DeclarativeBase, DeclarativeBaseNoMeta]]

logger = logging.getLogger(__name__)

_FieldTypesValues = tuple[str, str, MPT[str, object], MPT[str, object]]
FIELD_TYPES: MPT[type[sa.types.TypeEngine[Any]], _FieldTypesValues] = MPT({
    sa.Boolean: ("BooleanField", "BooleanInput", MPT({}), MPT({})),
    sa.Date: ("DateField", "DateInput", MPT({"showDate": True, "showTime": False}), MPT({})),
    sa.DateTime: ("DateField", "DateTimeInput",
                  MPT({"showDate": True, "showTime": True}), MPT({})),
    sa.Enum: ("SelectField", "SelectInput", MPT({}), MPT({})),
    sa.Integer: ("NumberField", "NumberInput", MPT({}), MPT({})),
    sa.Numeric: ("NumberField", "NumberInput", MPT({}), MPT({})),
    sa.String: ("TextField", "TextInput", MPT({}), MPT({})),
    sa.Time: ("TimeField", "TimeInput", MPT({}), MPT({})),
    sa.Uuid: ("TextField", "TextInput", MPT({}), MPT({})),  # TODO: validators
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


_Components = tuple[str, str, dict[str, object], dict[str, object]]


def get_components(t: sa.types.TypeEngine[object]) -> _Components:
    for key, (field, inp, field_props, input_props) in FIELD_TYPES.items():
        if isinstance(t, key):
            return (field, inp, field_props.copy(), input_props.copy())

    return ("TextField", "TextInput", {}, {})


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
                   filters: dict[str, object]) -> Iterator[_SABoolExpression]:
    return (columns[k].in_(v) if isinstance(v, list)
            else columns[k].ilike(f"%{v}%") if isinstance(v, str) else columns[k] == v
            for k, v in filters.items())


# ID is based on PK, which we can't infer from types, so must use Any here.
class SAResource(AbstractAdminResource[tuple[Any, ...]]):
    _model: Union[type[DeclarativeBase], type[DeclarativeBaseNoMeta], None] = None

    def __init__(self, db: AsyncEngine, model_or_table: _ModelOrTable):
        if isinstance(model_or_table, sa.Table):
            table = model_or_table
        else:
            if not isinstance(model_or_table.__table__, sa.Table):
                raise ValueError("Non-table mappings are not supported.")
            table = model_or_table.__table__
            self._model = model_or_table

        self._db = db
        self._table = table
        self.name = table.name
        self.primary_key = tuple(filter(lambda c: table.c[c].primary_key, self._table.c.keys()))
        if not self.primary_key:
            self.primary_key = tuple(self._table.c.keys())
        pk_types = tuple(table.c[pk].type.python_type for pk in self.primary_key)
        self._id_type = tuple.__class_getitem__(pk_types)  # type: ignore[assignment]

        self.fields = {}
        self.inputs = {}
        self.omit_fields = set()
        self._foreign_rows = {tuple(c.column_keys) for c in table.foreign_key_constraints}
        record_type = {}
        for c in table.c.values():
            if c.foreign_keys:
                field = "ReferenceField"
                inp = "ReferenceInput"
                constraint = next(cn for cn in table.foreign_key_constraints
                                  if cn.contains_column(c))
                key = next(iter(c.foreign_keys))
                label = c.name.replace("_", " ").title()
                keys = tuple((col.name, next(iter(col.foreign_keys)).column.name)
                             for col in constraint.columns)
                field_props: dict[str, Any] = {}
                inp_props: dict[str, Any] = {"referenceKeys": keys}
                props: dict[str, Any] = {"reference": key.column.table.name,
                                         "target": key.column.name, "label": label,
                                         "source": fk(*constraint.column_keys)}
            else:
                field, inp, field_props, inp_props = get_components(c.type)
                props = {"source": data(c.name)}

            if inp == "BooleanInput" and c.nullable:
                inp = "NullableBooleanInput"

            if isinstance(c.type, sa.Enum):
                props["choices"] = tuple({"id": e.value, "name": e.name}
                                         for e in c.type.python_type)

            length = getattr(c.type, "length", 0)
            if length is None or length > 31:
                props["fullWidth"] = True
                if length is None or length > 127:
                    inp_props["multiline"] = True

            if isinstance(c.default, sa.ColumnDefault):
                props["placeholder"] = c.default.arg

            if c.comment:
                props["helperText"] = c.comment

            field_props.update(props)
            self.fields[c.name] = comp(field, field_props)
            if c.computed is None:
                # TODO: Allow custom props (e.g. disabled, multiline, rows etc.)
                inp_props.update(props)
                show = c is not table.autoincrement_column
                inp_props["validate"] = self._get_validators(table, c)
                if inp == "NumberInput":
                    for v in inp_props["validate"]:
                        if v["name"] == "minValue":
                            inp_props["min"] = v["args"][0]
                        elif v["name"] == "maxValue":
                            inp_props["max"] = v["args"][0]
                self.inputs[c.name] = comp(inp, inp_props)  # type: ignore[assignment]
                self.inputs[c.name]["show_create"] = show
                field_type: Any = c.type.python_type
                if c.nullable:
                    field_type = Optional[field_type]
                record_type[c.name] = field_type

        if not isinstance(model_or_table, sa.Table):
            # Append fields to represent ORM relationships.
            # Mypy doesn't handle union well here.
            mapper = cast(Union[Mapper[DeclarativeBase], Mapper[DeclarativeBaseNoMeta]],
                          sa.inspect(model_or_table))
            assert mapper is not None  # noqa: S101
            for name, relationship in mapper.relationships.items():
                # https://github.com/sqlalchemy/sqlalchemy/discussions/10161#discussioncomment-6583442
                assert relationship.local_remote_pairs  # noqa: S101
                if not isinstance(relationship.entity.persist_selectable, sa.Table):
                    continue
                local, remotes = zip(*relationship.local_remote_pairs)

                self._foreign_rows.add(tuple(c.name for c in local))

                props = {"reference": relationship.entity.persist_selectable.name,
                         "label": name.title(), "source": fk(*(c.name for c in local)),
                         "target": fk(*(r.name for r in remotes)), "sortable": False}
                if any(c.foreign_keys for c in local):
                    t = "ReferenceField"
                    props["link"] = "show"
                elif relationship.uselist:
                    t = "ReferenceManyField"
                    props["reference"] = self.name
                    props["target"] = name
                    props["source"] = "id"
                    props["filter"] = {"__meta__": {"orm": True}}
                else:
                    t = "ReferenceOneField"
                    props["link"] = "show"

                children = []
                for kc in relationship.target.c.values():
                    if kc in remotes:  # Skip the foreign key
                        continue
                    field, _inp, c_fprops, _inp_props = get_components(kc.type)
                    c_fprops["source"] = data(kc.name)
                    children.append(comp(field, c_fprops))
                container = "Datagrid" if t == "ReferenceManyField" else "DatagridSingle"
                datagrid = comp(container, {"children": children, "rowClick": "show"})
                if t == "ReferenceManyField":
                    datagrid["props"]["bulkActionButtons"] = comp(
                        "BulkDeleteButton", {"mutationMode": "pessimistic"})
                props["children"] = datagrid

                self.fields[name] = comp(t, props)
                self.omit_fields.add(name)

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
    async def get_one(self, record_id: tuple[Any, ...], meta: Meta) -> Record:
        async with self._db.connect() as conn:
            stmt = sa.select(self._table).where(*self._cmp_pk(record_id))
            result = await conn.execute(stmt)
            return result.one()._asdict()

    @handle_errors
    async def get_many(self, record_ids: Sequence[tuple[Any, ...]], meta: Meta) -> list[Record]:
        async with self._db.connect() as conn:
            stmt = sa.select(self._table).where(self._cmp_pk_many(record_ids))
            result = await conn.execute(stmt)
            return [r._asdict() for r in result]

    async def get_many_ref_name(self, target: str, meta: Meta) -> str:
        if meta and meta.get("orm", False):
            # TODO(pydantic): arbitrary_types_allowed=True  check(_RelationshipAttr, ...)
            relationship = getattr(self._model, target)
            return relationship.entity.persist_selectable.name  # type: ignore[no-any-return]

        return self.name

    @handle_errors
    async def get_many_ref(self, params: GetManyRefParams) -> tuple[list[Record], int]:
        meta = params.get("meta")
        if meta and meta.get("orm", False):
            if self._model is None:
                raise web.HTTPBadRequest(reason="Not an ORM model.")

            # Use an ORM relationship to get the records (essentially the inverse of a
            # normal manyReference request). This makes it easy to support complex
            # relationships (such as many-to-many) without react-admin needing the details
            target = params["target"][0]
            reverse = params["sort"]["order"] == "DESC"
            # TODO(pydantic): arbitrary_types_allowed=True  check(_RelationshipAttr, ...)
            relationship = getattr(self._model, target)
            async with AsyncSession(self._db) as sess:
                result = await sess.get(self._model, params["id"],
                                        options=(selectinload(relationship),))
                records = [{c.name: getattr(r, c.name) for c in r.__table__.c}
                           for r in getattr(result, target)]
                records.sort(key=lambda r: r[params["sort"]["field"]], reverse=reverse)
                return records, len(records)

        for k, v in zip(params["target"], params["id"]):
            params["filter"][k] = v
        return await self.get_list(params)

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
    async def update(self, record_id: tuple[Any, ...], data: Record, previous_data: Record,
                     meta: Meta) -> Record:
        async with self._db.begin() as conn:
            stmt = sa.update(self._table).where(*self._cmp_pk(record_id))
            stmt = stmt.values(data).returning(*self._table.c)
            row = await conn.execute(stmt)
            return row.one()._asdict()

    @handle_errors
    async def update_many(self, record_ids: Sequence[tuple[Any, ...]], data: Record,
                          meta: Meta) -> list[tuple[Any, ...]]:
        async with self._db.begin() as conn:
            stmt = sa.update(self._table).where(self._cmp_pk_many(record_ids))
            stmt = stmt.values(data).returning(*(self._table.c[pk] for pk in self.primary_key))
            return list(await conn.scalars(stmt))

    @handle_errors
    async def delete(self, record_id: tuple[Any, ...], previous_data: Record,
                     meta: Meta) -> Record:
        async with self._db.begin() as conn:
            stmt = sa.delete(self._table).where(*self._cmp_pk(record_id))
            row = await conn.execute(stmt.returning(*self._table.c))
            return row.one()._asdict()

    @handle_errors
    async def delete_many(self, record_ids: Sequence[tuple[Any, ...]],
                          meta: Meta) -> list[tuple[Any, ...]]:
        async with self._db.begin() as conn:
            stmt = sa.delete(self._table).where(self._cmp_pk_many(record_ids))
            r = await conn.scalars(stmt.returning(*(self._table.c[pk] for pk in self.primary_key)))
            return list(r)

    def _cmp_pk(self, record_id: tuple[Any, ...]) -> Iterator[_SABoolExpression]:
        return (self._table.c[pk] == r_id for pk, r_id in zip(self.primary_key, record_id))

    def _cmp_pk_many(self, record_ids: Sequence[tuple[Any, ...]]) -> _SABoolExpression:
        return sa.tuple_(*(self._table.c[pk] for pk in self.primary_key)).in_(record_ids)

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
                if constr.sqltext.operator is not operator.and_:
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
                        if op is operator.ge:
                            validators.append(func("minValue", (right.value,)))
                        elif op is operator.gt:
                            validators.append(func("minValue", (right.value + 1,)))
                        elif op is operator.le:
                            validators.append(func("maxValue", (right.value,)))
                        elif op is operator.lt:
                            validators.append(func("maxValue", (right.value - 1,)))
                    elif isinstance(left, sa.Function):
                        if left.name == "char_length":
                            if next(iter(left.clauses)) is not c:
                                continue
                            if not isinstance(right, sa.BindParameter) or right.value is None:
                                continue
                            if op is operator.ge:
                                validators.append(func("minLength", (right.value,)))
                            elif op is operator.gt:
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
