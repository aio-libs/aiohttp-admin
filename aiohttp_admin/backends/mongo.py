import re
from bson import ObjectId

from ..resource import AbstractResource
from ..exceptions import ObjectNotFound
from ..utils import json_response, validate_query


__all__ = ['MotorResource']


def op(filter, field, operation, value):
    if operation == 'in':
        filter[field] = {'$in': value}
    elif operation == 'like':
        filter[field] = {'$regex': '^{}'.format(re.escape(value))}
    elif operation == 'eq':
        filter[field] = {'$eq': value}
    elif operation == 'ne':
        filter[field] = {'$not': value}
    elif operation == 'le':
        filter[field] = {'$lte': value}
    elif operation == 'lt':
        filter[field] = {'$lt': value}
    elif operation == 'ge':
        filter[field] = {'$gt': value}
    elif operation == 'gt':
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


class MotorResource(AbstractResource):

    def __init__(self, collection, schema, primary_key='_id', url=None):
        super().__init__(url)
        self._collection = collection
        self._primary_key = primary_key
        self._validator = schema

    @property
    def db(self):
        return self._db

    @property
    def pk(self):
        return self._pk

    async def list(self, request):
        q = validate_query(request.GET)

        page = q['_page']
        # sort_field = q['_sortField']
        per_page = q['_perPage']
        filters = q.get('_filters')

        # TODO: add sorting support
        # sort_dir = q['_sortDir']

        offset = (page - 1) * per_page
        limit = per_page
        if filters:
            query = create_filter(filters)
        query = {}
        cursor = self._collection.find(query).skip(offset).limit(limit)
        entities = await cursor.to_list(limit)
        count = await self._collection.find(query).count()
        headers = {'X-Total-Count': str(count)}
        return json_response(entities, headers=headers)

    async def detail(self, request):
        entity_id = request.match_info['entity_id']
        query = {self._primary_key: ObjectId(entity_id)}
        doc = await self._collection.find_one(query)
        if not doc:
            raise ObjectNotFound()

        entity = dict(doc)
        return json_response(entity)

    async def create(self, request):
        payload = await request.json()
        data = self._create_validator(payload)

        entity = dict(data)
        return json_response(entity)

    async def update(self, request):
        entity_id = request.match_info['entity_id']
        payload = await request.json()
        data = self._create_validator(payload)
        assert entity_id
        entity = dict(data)
        return json_response(entity)

    async def delete(self, request):
        entity_id = request.match_info['entity_id']
        assert entity_id
        return json_response({'status': 'deleted'})
