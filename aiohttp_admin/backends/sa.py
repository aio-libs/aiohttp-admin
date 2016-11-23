import sqlalchemy as sa

from ..resource import AbstractResource
from ..exceptions import ObjectNotFound
from ..security import require, Permissions
from ..utils import (json_response, validate_payload, validate_query,
                     calc_pagination, ASC)
from .sa_utils import table_to_trafaret, create_filter


__all__ = ['PGResource', 'MySQLResource']


class PGResource(AbstractResource):

    def __init__(self, db, table, primary_key='id', url=None):
        super().__init__(primary_key=primary_key, resource_name=url)
        self._db = db
        self._table = table
        self._primary_key = primary_key
        self._pk = table.c[primary_key]
        # TODO: do we ability to pass custom validator for table?
        self._create_validator = table_to_trafaret(table, primary_key,
                                                   skip_pk=True)
        self._update_validator = table_to_trafaret(table, primary_key,
                                                   skip_pk=True)

    @property
    def pool(self):
        return self._db

    @property
    def table(self):
        return self._table

    async def list(self, request):
        await require(request, Permissions.view)
        columns_names = list(self._table.c.keys())
        q = validate_query(request.GET, columns_names)
        paging = calc_pagination(q, self._primary_key)

        filters = q.get('_filters')
        async with self.pool.acquire() as conn:
            if filters:
                query = create_filter(self.table, filters)
            else:
                query = self.table.select()
            count = await conn.scalar(
                sa.select([sa.func.count()])
                .select_from(query.alias('foo')))

            sort_dir = sa.asc if paging.sort_dir == ASC else sa.desc
            cursor = await conn.execute(
                query
                .offset(paging.offset)
                .limit(paging.limit)
                .order_by(sort_dir(paging.sort_field)))

            recs = await cursor.fetchall()

            entities = list(map(dict, recs))

        headers = {'X-Total-Count': str(count)}
        return json_response(entities, headers=headers)

    async def detail(self, request):
        await require(request, Permissions.view)
        entity_id = request.match_info['entity_id']
        async with self.pool.acquire() as conn:
            query = self.table.select().where(self._pk == entity_id)
            resp = await conn.execute(query)
            rec = await resp.first()

        if not rec:
            msg = 'Entity with id: {} not found'.format(entity_id)
            raise ObjectNotFound(msg)

        entity = dict(rec)
        return json_response(entity)

    async def create(self, request):
        await require(request, Permissions.add)
        raw_payload = await request.read()
        data = validate_payload(raw_payload, self._create_validator)

        async with self.pool.acquire() as conn:
            query = self.table.insert().values(data).returning(*self.table.c)
            rec = await conn.execute(query)
            row = await rec.first()
            await conn.execute('commit;')

        entity = dict(row)
        return json_response(entity)

    async def update(self, request):
        await require(request, Permissions.edit)
        entity_id = request.match_info['entity_id']
        raw_payload = await request.read()
        data = validate_payload(raw_payload, self._update_validator)

        # TODO: execute in transaction?
        async with self.pool.acquire() as conn:
            query = self.table.select().where(self._pk == entity_id)
            row = await conn.execute(query)
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
            await conn.execute('commit;')

        entity = dict(rec)
        return json_response(entity)

    async def delete(self, request):
        await require(request, Permissions.delete)
        entity_id = request.match_info['entity_id']

        async with self.pool.acquire() as conn:
            query = self.table.delete().where(self._pk == entity_id)
            await conn.execute(query)
            # TODO: Think about autocommit by default
            await conn.execute('commit;')

        return json_response({'status': 'deleted'})


class MySQLResource(PGResource):

    async def create(self, request):
        await require(request, Permissions.add)
        raw_payload = await request.read()
        data = validate_payload(raw_payload, self._create_validator)

        async with self.pool.acquire() as conn:
            rec = await conn.execute(self.table.insert().values(data))
            new_entity_id = rec.lastrowid
            resp = await conn.execute(
                self.table.select()
                .where(self._pk == new_entity_id))
            rec = await resp.first()
            await conn.execute('commit;')

        entity = dict(rec)
        return json_response(entity)

    async def update(self, request):
        await require(request, Permissions.edit)
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

            await conn.execute(
                self.table.update()
                .values(data)
                .where(self._pk == entity_id))

            await conn.execute('commit;')
            resp = await conn.execute(
                self.table.select()
                .where(self._pk == entity_id))
            rec = await resp.first()

        entity = dict(rec)
        return json_response(entity)
