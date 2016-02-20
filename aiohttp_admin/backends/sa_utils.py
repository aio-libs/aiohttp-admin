import functools

import sqlalchemy as sa
import trafaret as t
from trafaret.contrib.rfc_3339 import DateTime
from sqlalchemy.dialects import postgresql


__all__ = ['validator_from_table']


def buield_trafaret(sa_type, **kwargs):

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
        item_trafaret = buield_trafaret(sa_type.item_type)
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
    field = buield_trafaret(column.type)
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
