import re
from collections import defaultdict
import trafaret as t
from trafaret.contrib.object_id import MongoId

from ..exceptions import JsonValidaitonError
from ..utils import MULTI_FIELD_TEXT_QUERY, as_dict


__all__ = ['create_validator', 'create_filter']


def op(filter, field, operation, value):
    if operation == 'in':
        filter[field].update({'$in': value})
    elif operation == 'like':
        filter[field].update({'$regex': '^{}'.format(re.escape(value))})
    elif operation == 'eq':
        filter[field].update({'$eq': value})
    elif operation == 'ne':
        filter[field].update({'$ne': value})
    elif operation == 'le':
        filter[field].update({'$lte': value})
    elif operation == 'lt':
        filter[field].update({'$lt': value})
    elif operation == 'gt':
        filter[field].update({'$gt': value})
    elif operation == 'ge':
        filter[field].update({'$gte': value})
    else:
        raise ValueError('Operation not supported {}'.format(operation))
    return filter


# TODO: fix comparators, keys should be something better
comparator_map = {
    t.String: ('eq', 'ne', 'like', 'in'),
    t.Int: ('eq', 'ne', 'lt', 'le', 'gt', 'ge', 'in'),
    t.Float: ('eq', 'ne', 'lt', 'le', 'gt', 'ge'),
    # t.Date: ('eq', 'ne', 'lt', 'le', 'gt', 'ge'),
}


def check_comparator(column, comparator):
    # TODO: fix error messages and types
    if type(column.type) not in comparator_map:
        msg = 'Filtering for column type {} not supported'.format(column.type)
        raise Exception(msg)

    if comparator not in comparator_map[type(column.type)]:
        msg = 'Filtering for column type {} not supported'.format(column.type)
        raise Exception(msg)


def apply_trafaret(trafaret, value):
    validate = trafaret.check_and_return

    if isinstance(trafaret, MongoId):
        validate = trafaret.converter

    if isinstance(value, list):
        try:
            value = validate(value)
        except t.DataError:
            value = [validate(v) for v in value]
    else:
        value = validate(value)
    return value


def _check_value(column_traf_map, field_name, value):
    # at this point we sure that field name is present in schema
    # validation should be done earlier
    trafaret = column_traf_map[field_name]

    try:
        value = apply_trafaret(trafaret, value)
    except t.DataError as exc:
        raise JsonValidaitonError(**as_dict(exc))

    return value


def text_filter(query, value, schema):
    string_columns = [s.name for s in schema.keys
                      if isinstance(s.trafaret, t.String)]
    query_list = []
    for column_name in string_columns:
        query_list.append(op(defaultdict(lambda: {}),
                             column_name,
                             "like",
                             value))
    query["$or"] = query_list
    return query


# TODO: use functional style to create query
# do not modify dict inside functions, modify dict on
# same level
def create_filter(filter, schema):
    column_traf_map = {s.name: s.trafaret for s in schema.keys}
    query = defaultdict(lambda: {})
    for field_name, operation in filter.items():
        # case for special q filter, {"q": "text"}
        if field_name == MULTI_FIELD_TEXT_QUERY:
            value = operation
            query = text_filter(query, value, schema)
            continue
        # special case {"key": "value"} check for equality
        if not isinstance(operation, dict):
            value = operation
            value = _check_value(column_traf_map, field_name, value)
            operation = {'eq': value}

        for op_name, value in operation.items():
            value = _check_value(column_traf_map, field_name, value)
            query = op(query, field_name, op_name, value)

    return query


def create_validator(schema, primary_key):
    # create validator without primary key, used for update queries
    # where pk supplied in url and rest in body
    keys = [s for s in schema.keys if s.get_name() != primary_key]
    new_schema = t.Dict({})
    new_schema.keys = keys
    return new_schema.ignore_extra(primary_key)
