import json
from functools import partial
from datetime import datetime, date

import trafaret as t
from aiohttp import web

from .exceptions import JsonValidaitonError
from .consts import TEMPLATES_ROOT


__all__ = ['json_response', 'validate_query', 'gather_template_folders']


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
    OptKey('ge'): t.String,
    OptKey('lt'): t.String,
    OptKey('le'): t.String,
    OptKey('ne'): t.String,
    OptKey('eq'): t.String,
    OptKey('like'): t.String,
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
    filters = query_dict.pop('_filters', None)
    if filters:
        try:
            f = json.loads(filters)
        except ValueError as e:
            raise t.DataError('_filters can not be serialised') from e
        else:
            query_dict['_filters'] = f

    try:
        q = ListQuery(query_dict)
    except t.DataError as exc:
        raise JsonValidaitonError(**exc.as_dict())

    return q


def gather_template_folders(template_folder):
    # gather template folders: default and provided
    if not isinstance(template_folder, list):
        template_folder = [template_folder]
    template_root = str(TEMPLATES_ROOT)
    if template_folder is None:
        template_folders = [template_root]
    else:
        template_folders = [template_root] + template_folder
    return template_folders
