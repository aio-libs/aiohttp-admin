import operator as _operator

import sqlalchemy as sa
import trafaret as t
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import or_
from trafaret.contrib.rfc_3339 import DateTime

from ..exceptions import JsonValidaitonError
from ..utils import MULTI_FIELD_TEXT_QUERY


__all__ = ['table_to_trafaret', 'create_filter']


AnyDict = t.Dict({}).allow_extra('*')


def build_trafaret(sa_type, **kwargs):

    if isinstance(sa_type, sa.sql.sqltypes.Enum):
        trafaret = t.Enum(*sa_type.enums, **kwargs)

    # check for Text should be before String
    elif isinstance(sa_type, sa.sql.sqltypes.Text):
        trafaret = t.String(**kwargs)

    elif isinstance(sa_type, sa.sql.sqltypes.String):
        trafaret = t.String(max_length=sa_type.length, **kwargs)

    elif isinstance(sa_type, sa.sql.sqltypes.Integer):
        trafaret = t.Int(**kwargs)

    elif isinstance(sa_type, sa.sql.sqltypes.Float):
        trafaret = t.Float(**kwargs)

    elif isinstance(sa_type, sa.sql.sqltypes.DateTime):
        trafaret = DateTime(**kwargs)  # RFC3339

    elif isinstance(sa_type, sa.sql.sqltypes.Date):
        trafaret = DateTime(**kwargs)  # RFC3339

    elif isinstance(sa_type, sa.sql.sqltypes.Boolean):
        trafaret = t.StrBool(**kwargs)

    # Add PG related JSON and ARRAY
    elif isinstance(sa_type, postgresql.JSON):
        trafaret = AnyDict | t.List(AnyDict)

    # Add PG related JSON and ARRAY
    elif isinstance(sa_type, postgresql.ARRAY):
        item_trafaret = build_trafaret(sa_type.item_type)
        trafaret = t.List(item_trafaret)

    else:
        type_ = str(sa_type)
        msg = 'Validator for type {} not implemented'.format(type_)
        raise NotImplementedError(msg)
    return trafaret


_empty = object()


def build_key(name, default=_empty):
    if default is not _empty:
        key = t.Key(name, default=default)
    else:
        key = t.Key(name)
    return key


def build_field(column):
    field = build_trafaret(column.type)
    if column.nullable:
        field |= t.Null
    return field


def table_to_trafaret(table, primary_key, skip_pk=False):
    trafaret = {}
    for name, column in table.c.items():
        if skip_pk and column.name == primary_key:
            continue
        key = name
        default = column.server_default
        key = build_key(name, default)

        traf_field = build_field(column)
        trafaret[key] = traf_field
    return t.Dict(trafaret).ignore_extra(primary_key)


def to_column(column_name, table):
    c = table.c[column_name]
    return c


def op(operation, column):
    if operation == 'in':
        def comparator(column, v):
            return column.in_(v)
    elif operation == 'like':
        def comparator(column, v):
            return column.like(v + '%')
    elif operation == 'eq':
        comparator = _operator.eq
    elif operation == 'ne':
        comparator = _operator.ne
    elif operation == 'le':
        comparator = _operator.le
    elif operation == 'lt':
        comparator = _operator.lt
    elif operation == 'ge':
        comparator = _operator.ge
    elif operation == 'gt':
        comparator = _operator.gt
    else:
        raise ValueError('Operation {} not supported'.format(operation))
    return comparator


# TODO: fix comparators, keys should be something better
comparator_map = {
    sa.sql.sqltypes.String: ('eq', 'ne', 'like', 'in'),
    sa.sql.sqltypes.Text: ('eq', 'ne', 'like'),
    sa.sql.sqltypes.Integer: ('eq', 'ne', 'lt', 'le', 'gt', 'ge', 'in'),
    sa.sql.sqltypes.Float: ('eq', 'ne', 'lt', 'le', 'gt', 'ge'),
    sa.sql.sqltypes.Date: ('eq', 'ne', 'lt', 'le', 'gt', 'ge'),
}


def check_comparator(column, comparator):
    if type(column.type) not in comparator_map:
        msg = 'Filtering for column type {} not supported'.format(column.type)
        raise JsonValidaitonError(msg)

    if comparator not in comparator_map[type(column.type)]:
        msg = 'Filtering for column type {} not supported'.format(column.type)
        raise JsonValidaitonError(msg)


def check_value(column, value):
    trafaret = build_trafaret(column.type)
    try:
        if isinstance(value, list):
            value = [trafaret.check_and_return(v) for v in value]
        else:
            value = trafaret.check_and_return(value)

    except t.DataError as exc:
        raise JsonValidaitonError(**exc.as_dict())
    return value


def text_filter(query, value, table):
    pairs = ((n, c) for n, c in table.c.items()
             if isinstance(c.type, sa.sql.sqltypes.String))
    sub_queries = []
    for name, column in pairs:
        do_compare = op("like", column)
        sub_queries.append(do_compare(column, value))

    query = query.where(or_(*sub_queries))
    return query


# TODO: validate that value supplied in filter has same type as in table
# TODO: use functional style to create query
def create_filter(table, filter):
    query = table.select()

    for column_name, operation in filter.items():

        if column_name == MULTI_FIELD_TEXT_QUERY:
            value = operation
            query = text_filter(query, value, table)
            continue

        column = to_column(column_name, table)

        if not isinstance(operation, dict):
            value = operation
            operation = {'eq': value}

        for op_name, value in operation.items():
            check_comparator(column, op_name)
            value = check_value(column, value)
            do_compare = op(op_name, column)
            f = do_compare(column, value)
            query = query.where(f)

    return query
