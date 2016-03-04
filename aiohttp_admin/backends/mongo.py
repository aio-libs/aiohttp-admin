from bson import ObjectId

from ..resource import AbstractResource
from ..exceptions import ObjectNotFound
from ..utils import json_response, validate_query, validate_payload
from .mongo_utils import create_validator, create_filter


__all__ = ['MotorResource']


class MotorResource(AbstractResource):

    def __init__(self, collection, schema, primary_key='_id', url=None):
        super().__init__(url)
        self._collection = collection
        self._primary_key = primary_key
        self._schema = create_validator(schema, primary_key)

    async def list(self, request):
        q = validate_query(request.GET)

        page = q['_page']
        per_page = q['_perPage']

        sort_field = q.get('_sortField', self._primary_key)
        sort_dir = q['_sortDir']
        filters = q.get('_filters')

        offset = (page - 1) * per_page
        limit = per_page

        query = {}
        if filters:
            query = create_filter(filters)
        sort_direction = ASCENDING if sort_dir == ASC else DESCENDING

        cursor = (self._collection.find(query)
                  .skip(offset)
                  .limit(limit)
                  .sort(sort_field, sort_direction))

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
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)

        entity = dict(doc)
        return json_response(entity)

    async def create(self, request):
        raw_payload = await request.read()
        data = validate_payload(raw_payload, self._schema)

        entity_id = await self._collection.insert(data)
        query = {self._primary_key: ObjectId(entity_id)}
        doc = await self._collection.find_one(query)

        return json_response(doc)

    async def update(self, request):
        entity_id = request.match_info['entity_id']
        raw_payload = await request.read()
        data = validate_payload(raw_payload, self._schema)
        query = {self._primary_key: ObjectId(entity_id)}

        doc = await self._collection.find_and_modify(
            query, {"$set": data}, upsert=False, new=True)

        if not doc:
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)

        return json_response(doc)

    async def delete(self, request):
        entity_id = request.match_info['entity_id']
        # TODO: fix ObjectId is not always valid case
        query = {self._primary_key: ObjectId(entity_id)}
        await self._collection.remove(query)
        return json_response({'status': 'deleted'})
