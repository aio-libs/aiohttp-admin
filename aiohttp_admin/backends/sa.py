import sqlalchemy as sa

from ..resource import AbstractResource
from ..exceptions import ObjectNotFound
from ..utils import json_response, validate_payload
from .sa_utils import validator_from_table, create_filter, validate_query


__all__ = ['SAResource']


class SAResource(AbstractResource):

    def __init__(self, db, table, primary_key='id', url=None):
        super().__init__(url)
        self._pg = db
        self._table = table
        self._primary_key = primary_key
        self._pk = table.c[primary_key]
        # TODO: do we ability to pass custom validator for table?
        self._create_validator = validator_from_table(table, primary_key,
                                                      skip_pk=True)
        self._update_validator = validator_from_table(table, primary_key,
                                                      skip_pk=True)

    @property
    def pool(self):
        return self._pg

    @property
    def table(self):
        return self._table

    async def list(self, request):
        q = validate_query(request.GET, self._table)

        page = q['_page']
        sort_field = q.get('_sortField', self._primary_key)
        per_page = q['_perPage']
        sort_dir = q['_sortDir']

        filters = q.get('_filters')

        offset = (page - 1) * per_page
        limit = per_page
        async with self.pool.acquire() as conn:
            if filters:
                query = create_filter(self.table, filters)
            else:
                query = self.table.select()
            count = await conn.scalar(
                sa.select([sa.func.count()])
                .select_from(query.alias('foo')))

            sort_dir = sa.asc if sort_dir == 'ASC' else sa.desc
            cursor = await conn.execute(
                query
                .offset(offset)
                .limit(limit)
                .order_by(sort_dir(sort_field)))

            recs = await cursor.fetchall()

            entities = list(map(dict, recs))

        headers = {'X-Total-Count': str(count)}
        return json_response(entities, headers=headers)

    async def detail(self, request):
        entity_id = request.match_info['entity_id']

        async with self.pool.acquire() as conn:
            resp = await conn.execute(
                self.table.select().where(self._pk == entity_id))
            rec = await resp.first()

        if not rec:
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)

        entity = dict(rec)
        return json_response(entity)

    async def create(self, request):
        raw_payload = await request.read()
        data = validate_payload(raw_payload, self._create_validator)

        async with self.pool.acquire() as conn:
            rec = await conn.execute(
                self.table.insert().values(data).returning(*self.table.c))
            row = await rec.first()

        entity = dict(row)
        return json_response(entity)

    async def update(self, request):
        entity_id = request.match_info['entity_id']
        raw_payload = await request.read()
        data = validate_payload(raw_payload, self._update_validator)

        # TODO: execute in transaction?
        async with self.pool.acquire() as conn:
            row = await conn.execute(
                self.table.select()
                .where(self._pk == entity_id)
            )
            rec = await row.first()
            if not rec:
                msg = 'Entity with id: {} not found'.format(entity_id)
                raise ObjectNotFound(msg)

            row = await conn.execute(
                self.table.update()
                .values(data)
                .returning(*self.table.c)
                .where(self._pk == entity_id))
            rec = await row.first()

        entity = dict(rec)
        return json_response(entity)

    async def delete(self, request):
        entity_id = request.match_info['entity_id']

        async with self.pool.acquire() as conn:
            await conn.execute(
                self.table.delete().where(self._pk == entity_id))

        return json_response({'status': 'deleted'})
