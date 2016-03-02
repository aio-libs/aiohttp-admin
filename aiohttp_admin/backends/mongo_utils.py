import re
import trafaret as t


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


def create_filter(filter):
    query = {}
    for field_name, operation in filter.items():
        if isinstance(operation, dict):
            for op_name, value in operation.items():
                query = op(query, field_name, op_name, value)
        else:
            value = operation
            query[field_name] = value
    return query


def create_validator(schema, primary_key):
    keys = [s for s in schema.keys if s.get_name() != primary_key]
    new_schema = t.Dict({})
    new_schema.keys = keys
    return new_schema
