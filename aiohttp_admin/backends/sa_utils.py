import functools
import operator as _operator

import sqlalchemy as sa
import trafaret as t
from trafaret.contrib.rfc_3339 import DateTime
from sqlalchemy.dialects import postgresql


__all__ = ['validator_from_table', 'create_filter', 'build_sa_fe_field']


def build_trafaret(sa_type, **kwargs):

    if isinstance(sa_type, sa.sql.sqltypes.Enum):
        trafaret = t.Enum(*sa_type.enums, **kwargs)

    elif isinstance(sa_type, sa.sql.sqltypes.String):
        trafaret = t.String(max_length=sa_type.length, **kwargs)

    elif isinstance(sa_type, sa.sql.sqltypes.Text):
        trafaret = t.String(**kwargs)

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
        trafaret = t.Dict({}).allow_extra('*')

    # Add PG related JSON and ARRAY
    elif isinstance(sa_type, postgresql.ARRAY):
        item_trafaret = build_trafaret(sa_type.item_type)
        trafaret = t.List(item_trafaret)

    else:
        type_ = str(sa_type)
        msg = 'Validator for type {} not implemented'.format(type_)
        raise NotImplementedError(msg)
    return trafaret


def build_key(name, default):
    if default is not None:
        Key = functools.partial(t.Key, default=default)
        key = Key(name)
    else:
        key = t.Key(name)
    return key


def build_field(column):
    field = build_trafaret(column.type)
    if column.nullable:
        field |= t.Null
    return field


def validator_from_table(table, skip_pk=False):
    trafaret = {}
    for name, column in table.c.items():
        if column.primary_key and skip_pk:
            continue
        key = name
        default = column.server_default
        key = build_key(name, default)

        traf_field = build_field(column)
        trafaret[key] = traf_field
    return t.Dict(trafaret)


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
        comparator = _operator.en
    elif operation == 'le':
        comparator = _operator.le
    elif operation == 'lt':
        comparator = _operator.lt
    elif operation == 'ge':
        comparator == _operator.ge
    elif operation == 'gt':
        comparator == _operator.gt
    else:
        raise ValueError('Operation {} not supported'.format(operation))
    return comparator


comparator_map = {
    sa.sql.sqltypes.String: ['eq', 'nq', 'like'],
    sa.sql.sqltypes.Text: ['eq', 'nq', 'like'],
    sa.sql.sqltypes.Integer: ['eq', 'nq', 'lt', 'le', 'gt', 'ge', 'in'],
    sa.sql.sqltypes.Float: ['eq', 'nq', 'lt', 'le', 'gt', 'ge'],
    sa.sql.sqltypes.Date: ['eq', 'nq', 'lt', 'le', 'gt', 'ge'],
}


def check_comparator(column, comparator):
    # TODO: fix error messages and types
    if column.type not in comparator_map:
        msg = 'Filtering for column type {} not supported'.format(column.type)
        raise Exception(msg)

    if comparator not in comparator_map[column.type]:
        msg = 'Filtering for column type {} not supported'.format(column.type)
        raise Exception(msg)


# TODO: simplify this monster
def create_filter(table, filter):
    query = table.select()

    for column_name, operation in filter.items():
        column = to_column(column_name, table)

        if isinstance(operation, dict):
            for op_name, value in operation.items():
                check_comparator(column, op_name)
                f = op(op_name, column)(column, value)
                query = query.where(f)
        else:
            value = operation
            query = query.where(column == value)
    return query


def build_type_mapper(sa_type, **kwargs):

    if isinstance(sa_type, sa.sql.sqltypes.Enum):
        fe_type = 'string'

    elif isinstance(sa_type, sa.sql.sqltypes.String):
        fe_type = 'string'

    elif isinstance(sa_type, sa.sql.sqltypes.Text):
        fe_type = 'text'

    elif isinstance(sa_type, sa.sql.sqltypes.Integer):
        fe_type = 'string'

    elif isinstance(sa_type, sa.sql.sqltypes.Float):
        fe_type = 'float'

    elif isinstance(sa_type, sa.sql.sqltypes.DateTime):
        fe_type = 'datetime'

    elif isinstance(sa_type, sa.sql.sqltypes.Date):
        fe_type = 'date'

    elif isinstance(sa_type, sa.sql.sqltypes.Boolean):
        fe_type = 'boolean'

    # Add PG related JSON and ARRAY
    elif isinstance(sa_type, postgresql.JSON):
        fe_type = 'json'

    # Add PG related JSON and ARRAY
    elif isinstance(sa_type, postgresql.ARRAY):
        fe_type = 'embedded_list'

    else:
        type_ = str(sa_type)
        msg = 'Validator for type {} not implemented'.format(type_)
        raise NotImplementedError(msg)

    return fe_type


def build_sa_fe_field(column):
    field = build_type_mapper(column)

    return field
