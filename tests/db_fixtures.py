import datetime

import aiomysql.sa
import aiopg.sa
import motor.motor_asyncio as aiomotor
import pytest
import sqlalchemy as sa
import trafaret as t

# from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable, DropTable
from trafaret.contrib.object_id import MongoId
from trafaret.contrib.rfc_3339 import DateTime


ADMIN_TYPE_LIST = 'pg', 'mongo', 'mysql'


@pytest.fixture
def admin_type():
    # 'pg', 'mysql', 'mongo'
    return 'pg'


@pytest.fixture
def database(request, admin_type):
    if admin_type == 'mysql':
        f = request.getfixturevalue('mysql')
    else:
        f = request.getfixturevalue('postgres')
    return f


@pytest.fixture
def mysql(request, loop, mysql_params):
    async def init_mysql(conf, loop):
        engine = await aiomysql.sa.create_engine(
            db=conf['database'],
            user=conf['user'],
            password=conf['password'],
            host=conf['host'],
            port=conf['port'],
            minsize=1,
            maxsize=2,
            loop=loop)
        return engine
    engine = loop.run_until_complete(init_mysql(mysql_params, loop))

    def fin():
        engine.close()
        loop.run_until_complete(engine.wait_closed())
    request.addfinalizer(fin)
    return engine


@pytest.fixture
def postgres(request, loop, pg_params):
    async def init_postgres(conf, loop):
        engine = await aiopg.sa.create_engine(
            database=conf['database'],
            user=conf['user'],
            password=conf['password'],
            host=conf['host'],
            port=conf['port'],
            minsize=1,
            maxsize=2,
            loop=loop)
        return engine
    engine = loop.run_until_complete(init_postgres(pg_params, loop))

    def fin():
        engine.close()
        loop.run_until_complete(engine.wait_closed())
    request.addfinalizer(fin)
    return engine


@pytest.fixture
def sa_table():
    choices = ['a', 'b', 'c']
    meta = sa.MetaData()
    post = sa.Table(
        'test_post', meta,
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('category', sa.String(200), nullable=True),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('views', sa.Integer, nullable=False),
        sa.Column('average_note', sa.Float, nullable=False),
        # sa.Column('pictures', postgresql.JSON, server_default='{}'),
        sa.Column('published_at', sa.DateTime, nullable=False),
        # sa.Column('tags', postgresql.ARRAY(sa.Integer), server_default='{}'),
        sa.Column('status',
                  sa.Enum(*choices, name="enum_name", native_enum=False),
                  server_default="a", nullable=False),
        sa.Column('visible', sa.Boolean, nullable=False),

        # Indexes #
        sa.PrimaryKeyConstraint('id', name='post_id_pkey'))
    return post


@pytest.fixture
def create_entries():
    def f(rows):
        values = []
        for i in range(rows):
            values.append({
                'title': 'title {}'.format(i),
                'category': 'category field {}'.format(i),
                'body': 'body field {}'.format(i),
                'views': i,
                'average_note': i * 0.1,
                # json is not supported in released sqlalchemy for mysql 5.7
                # 'pictures': {'foo': 'bar', 'i': i},
                'published_at': datetime.datetime.now(),
                # lists not supported in MySQL
                # 'tags': [i + 1, i + 2],
                'status': 'c',
                'visible': bool(i % 2),
            })
        return values
    return f


@pytest.yield_fixture
def create_table(request, sa_table, database, loop, create_entries):
    async def f(rows):
        create_expr = CreateTable(sa_table)
        async with database.acquire() as conn:
            await conn.execute(create_expr)
            values = create_entries(rows)
            query1 = sa_table.insert().values(values)
            await conn.execute(query1)
            await conn.execute('commit;')
        return sa_table

    yield f

    async def fin():
        drop_expr = DropTable(sa_table)
        async with database.acquire() as conn:
            await conn.execute(drop_expr)
            await conn.execute('commit;')

    loop.run_until_complete(fin())


@pytest.fixture
def document_schema():
    choices = ['a', 'b', 'c']
    schema = t.Dict({
        t.Key('_id'): MongoId,
        t.Key('title'): t.String(max_length=200),
        t.Key('category'): t.String(max_length=200),
        t.Key('body'): t.String,
        t.Key('views'): t.Int,
        t.Key('average_note'): t.Float,
        # t.Key('pictures'): t.Dict({}).allow_extra('*'),
        t.Key('published_at'): DateTime,
        # t.Key('tags'): t.List(t.Int),
        t.Key('status'): t.Enum(*choices),
        t.Key('visible'): t.StrBool,
    })
    return schema


@pytest.fixture
def mongo(request, loop, mongo_params):
    conf = mongo_params.copy()
    conf["database"] = "aiohttp_admin_db"
    conf["max_pool_size"] = 2

    async def init_mogo(conf, loop):
        url = "mongodb://{}:{}".format(conf['host'], conf['port'])
        conn = aiomotor.AsyncIOMotorClient(
            url, maxPoolSize=conf['max_pool_size'], io_loop=loop)
        return conn

    conn = loop.run_until_complete(init_mogo(conf, loop))

    def fin():
        conn.close()

    request.addfinalizer(fin)

    db = conf['database']
    return conn[db]


@pytest.fixture
def mongo_collection(mongo):
    name = 'posts'
    return mongo[name]


@pytest.yield_fixture
def create_document(request, document_schema, mongo_collection, loop,
                    create_entries):
    async def f(rows):
        await mongo_collection.drop()
        values = create_entries(rows)
        for doc in values:
            await mongo_collection.insert(doc)
        return sa_table
    yield f
    loop.run_until_complete(mongo_collection.drop())
