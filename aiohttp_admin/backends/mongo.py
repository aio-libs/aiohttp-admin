from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from ..exceptions import ObjectNotFound
from ..resource import AbstractResource
from ..security import require, Permissions
from ..utils import (json_response, validate_payload, ASC, validate_query,
                     calc_pagination)
from .mongo_utils import create_validator, create_filter


__all__ = ['MotorResource']


class MotorResource(AbstractResource):

    def __init__(self, collection, schema, primary_key='_id', url=None):
        super().__init__(primary_key=primary_key, resource_name=url)
        self._collection = collection
        self._primary_key = primary_key
        self._schema = schema
        self._update_schema = create_validator(schema, primary_key)

    @property
    def primary_key(self):
        return self._primary_key

    async def list(self, request):
        await require(request, Permissions.view)
        possible_fields = [k.name for k in self._schema.keys]
        q = validate_query(request.GET, possible_fields)
        paging = calc_pagination(q, self._primary_key)

        filters = q.get('_filters')
        query = {}
        if filters:
            query = create_filter(filters, self._schema)

        sort_direction = ASCENDING if paging.sort_dir == ASC else DESCENDING

        cursor = (self._collection.find(query)
                  .skip(paging.offset)
                  .limit(paging.limit)
                  .sort(paging.sort_field, sort_direction))

        entities = await cursor.to_list(paging.limit)
        count = await self._collection.find(query).count()
        headers = {'X-Total-Count': str(count)}
        return json_response(entities, headers=headers)

    async def detail(self, request):
        await require(request, Permissions.view)
        entity_id = request.match_info['entity_id']
        query = {self._primary_key: ObjectId(entity_id)}

        doc = await self._collection.find_one(query)
        if not doc:
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)

        entity = dict(doc)
        return json_response(entity)

    async def create(self, request):
        await require(request, Permissions.add)
        raw_payload = await request.read()
        data = validate_payload(raw_payload, self._update_schema)

        entity_id = await self._collection.insert(data)
        query = {self._primary_key: ObjectId(entity_id)}
        doc = await self._collection.find_one(query)

        return json_response(doc)

    async def update(self, request):
        await require(request, Permissions.edit)
        entity_id = request.match_info['entity_id']
        raw_payload = await request.read()
        data = validate_payload(raw_payload, self._update_schema)
        query = {self._primary_key: ObjectId(entity_id)}

        doc = await self._collection.find_and_modify(
            query, {"$set": data}, upsert=False, new=True)

        if not doc:
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)

        return json_response(doc)

    async def delete(self, request):
        await require(request, Permissions.delete)
        entity_id = request.match_info['entity_id']
        # TODO: fix ObjectId is not always valid case
        query = {self._primary_key: ObjectId(entity_id)}
        await self._collection.remove(query)
        return json_response({'status': 'deleted'})
