import json
from functools import partial
from datetime import datetime, date
import operator

from aiohttp import web
import trafaret as t


__all__ = ['json_response']


def json_datetime_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


_dumps = partial(json.dumps, default=json_datetime_serial)

json_response = partial(web.json_response, dumps=_dumps)


OptKey = partial(t.Key, optional=True)


Filter = t.Dict({
    OptKey('in'): t.List(t.String),
    OptKey('gt'): t.String,
    OptKey('gte'): t.String,
    OptKey('lt'): t.String,
    OptKey('lte'): t.String,
})

SimpleType = t.Int | t.Bool | t.String | t.Float
ListQuery = t.Dict({
    t.Key('_page', default=1): t.Int[0:],
    t.Key('_perPage', default=30): t.Int[0:],
    OptKey('_sortField', default='id'): t.String,
    OptKey('_sortDir'): t.Enum('DESC', 'ASC'),
    OptKey('_filters'): t.Mapping(t.String, Filter | SimpleType)
})




def validate_query(query):
    query_dict = dict(query)
    filters = query.get('_filters')
    if filters is not None:
        try:
            f = json.loads(filters)
        except ValueError as e:
            raise t.DataError('_filters can not be serialised') from e
        else:
            query_dict['_filters'] = f
    q = ListQuery(query_dict)
    return q
