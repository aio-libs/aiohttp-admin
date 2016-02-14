import operator as _operator
import sqlalchemy as sa

from ..resource import AbstractResource
from ..exceptions import ObjectNotFound
from ..utils import json_response, validate_query


def to_column(column_name, table):
    c = table.c[column_name]
    return c


def op(name, column):
    if name == 'in':
        def comparator(column, v):
            return column.in_(v)
    elif name == 'like':
        def comparator(column, v):
            return column.like(v + '%')
    elif name == 'eq':
        comparator = _operator.eq
    elif name == 'ne':
        comparator = _operator.en
    elif name == 'le':
        comparator = _operator.le
    elif name == 'lt':
        comparator = _operator.lt
    elif name == 'ge':
        comparator == _operator.ge
    elif name == 'gt':
        comparator == _operator.gt
    return comparator


def create_filter(table, filter):
    query = table.select()

    for column_name, operation in filter.items():
        column = to_column(column_name, table)

        if isinstance(operation, dict):
            for op_name, value in operation.items():
                f = op(op_name, column)(column, value)
                query = query.where(f)
        else:
            value = operation
            query = query.where(column == value)
    return query


class SAResource(AbstractResource):

    def __init__(self, db, table, primary_key='id', url=None):
        super().__init__(url)
        self._pg = db
        self._table = table
        self._primary_key = primary_key
        self._pk = to_column(primary_key, self._table)

    @property
    def pg(self):
        return self._pg

    @property
    def table(self):
        return self._table

    @property
    def pk(self):
        return self._pk

    async def list(self, request):
        q = validate_query(request.GET)

        page = q['_page']
        sort_field = q['_sortField']
        per_page = q['_perPage']
        filters = q.get('_filters')

        # TODO: add sorting support
        # sort_dir = q['_sortDir']

        offset = (page - 1) * per_page
        limit = per_page
        async with self.pg.acquire() as conn:
            if filters:
                query = create_filter(self.table, filters)
            else:
                query = self.table.select()
            count = await conn.scalar(
                sa.select([sa.func.count()])
                .select_from(query.alias('foo')))

            cursor = await conn.execute(
                query
                .offset(offset)
                .limit(limit)
                .order_by(sort_field))

            recs = await cursor.fetchall()

            entities = list(map(dict, recs))

        headers = {'X-Total-Count': str(count)}
        return json_response(entities, headers=headers)

    async def detail(self, request):
        entity_id = request.match_info['entity_id']

        async with self.pg.acquire() as conn:
            resp = await conn.execute(
                self.table.select().where(self.pk == entity_id))
            rec = await resp.first()

        if not rec:
            raise ObjectNotFound()

        entity = dict(rec)
        return json_response(entity)

    async def create(self, request):
        data = await request.json()

        async with self.pg.acquire() as conn:
            rec = await conn.execute(
                self.table.insert().values(data).returning(*self.table.c))
            row = await rec.first()

        entity = dict(row)
        return json_response(entity)

    async def update(self, request):
        entity_id = request.match_info['entity_id']

        payload = await request.json()
        async with self.pg.acquire() as conn:
            row = await conn.execute(
                self.table.select()
                .where(self.pk == entity_id)
            )
            rec = await row.first()
            if not rec:
                raise ObjectNotFound()

            row = await conn.execute(
                self.table.update()
                .values(payload)
                .returning(*self.table.c)
                .where(self.pk == entity_id))
            rec = await row.first()

        entity = dict(rec)
        return json_response(entity)

    async def delete(self, request):
        entity_id = request.match_info['entity_id']

        async with self.pg.acquire() as conn:

            await conn.execute(
                self.table.delete().where(self.pk == entity_id))

        return json_response({'status': 'deleted'})
