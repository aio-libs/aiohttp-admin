import re
import trafaret as t
from trafaret.contrib.object_id import MongoId

from ..exceptions import JsonValidaitonError
from ..utils import validate_query as _validate_query


__all__ = ['create_validator', 'create_filter']


def op(filter, field, operation, value):
    if operation == 'in':
        filter[field] = {'$in': value}
    elif operation == 'like':
        filter[field] = {'$regex': '^{}'.format(re.escape(value))}
    elif operation == 'eq':
        filter[field] = {'$eq': value}
    elif operation == 'ne':
        filter[field] = {'$ne': value}
    elif operation == 'le':
        filter[field] = {'$lte': value}
    elif operation == 'lt':
        filter[field] = {'$lt': value}
    elif operation == 'gt':
        filter[field] = {'$gt': value}
    elif operation == 'ge':
        filter[field] = {'$gte': value}
    else:
        raise ValueError('Operation not supported {}'.format(operation))
    return filter


# TODO: fix comparators, keys should be something better
comparator_map = {
    t.String: ['eq', 'ne', 'like'],
    t.Int: ['eq', 'ne', 'lt', 'le', 'gt', 'ge', 'in'],
    t.Float: ['eq', 'ne', 'lt', 'le', 'gt', 'ge'],
    # t.Date: ['eq', 'ne', 'lt', 'le', 'gt', 'ge'],
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
        raise JsonValidaitonError(**exc.as_dict())

    return value


def create_filter(filter, schema):
    column_traf_map = {s.name: s.trafaret for s in schema.keys}
    query = {}
    for field_name, operation in filter.items():
        if isinstance(operation, dict):
            for op_name, value in operation.items():
                value = _check_value(column_traf_map, field_name, value)
                query = op(query, field_name, op_name, value)
        else:
            value = operation
            value = _check_value(column_traf_map, field_name, value)
            query[field_name] = value
    return query


def create_validator(schema, primary_key):
    keys = [s for s in schema.keys if s.get_name() != primary_key]
    new_schema = t.Dict({})
    new_schema.keys = keys
    return new_schema


def validate_query(query, schema):
    possible_columns = set(k.name for k in schema.keys)
    q = _validate_query(query)
    sort_field = q.get('_sortField')

    filters = q.get('_filters', [])
    columns = [field_name for field_name in filters]

    if sort_field is not None:
        columns.append(sort_field)

    not_valid = set(columns).difference(possible_columns)
    if not_valid:
        column_list = ', '.join(not_valid)
        msg = 'Columns: {} do not present in resource'.format(column_list)
        raise JsonValidaitonError(msg)
    return q
