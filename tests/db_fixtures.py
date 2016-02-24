import datetime

import pytest
import aiopg.sa
import motor.motor_asyncio as aiomotor

import sqlalchemy as sa
from sqlalchemy.schema import CreateTable, DropTable
from sqlalchemy.dialects import postgresql


@pytest.fixture
def pg_conf():
    conf = {"database": "admindemo_blog",
            "user": "admindemo_user",
            "host": "localhost",
            "password": "admindemo_user",
            "port": 5432,
            "minsize": 1,
            "maxsize": 3}
    return conf


@pytest.fixture
def postgres(request, loop, pg_conf):
    async def init_postgres(conf, loop):
        engine = await aiopg.sa.create_engine(
            database=conf['database'],
            user=conf['user'],
            password=conf['password'],
            host=conf['host'],
            port=conf['port'],
            minsize=conf['minsize'],
            maxsize=conf['maxsize'],
            loop=loop)
        return engine
    engine = loop.run_until_complete(init_postgres(pg_conf, loop))

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
        sa.Column('pictures', postgresql.JSON, server_default='{}'),
        sa.Column('published_at', sa.DateTime, nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.Integer), server_default='{}'),
        sa.Column('status',
                  sa.Enum(*choices, name="enum_name", native_enum=False),
                  server_default="a", nullable=False),

        # Indexes #
        sa.PrimaryKeyConstraint('id', name='post_id_pkey'))
    return post


@pytest.fixture
def table(request, sa_table, postgres, loop):
    async def f():
        create_expr = CreateTable(sa_table)
        drop_expr = DropTable(sa_table)
        async with postgres.acquire() as conn:
            await conn.execute(drop_expr)
            await conn.execute(create_expr)
            query1 = sa_table.insert().values({
                'title': 'title field',
                'category': 'category field',
                'body': 'body field',
                'views': 42,
                'average_note': 7.8,
                'pictures': {'foo': 'bar'},
                'published_at': datetime.datetime.now(),
                'tags': [1, 2, 3],
                'status': 'c',
            })
            query2 = sa_table.insert().values({
                'title': 'title field 2',
                'body': 'body field',
                'views': 43,
                'average_note': 7.8,
                'pictures': {'foo': 'bar'},
                'published_at': datetime.datetime.now(),
                'tags': [5, 6, 7],
            })
            await conn.execute(query1)
            await conn.execute(query2)
    loop.run_until_complete(f())
    return sa_table


@pytest.fixture
def mongo_conf():
    conf = {"database": "aiohttp_admin_db",
            "host": "127.0.0.1",
            "port": 27017,
            "max_pool_size": 3}
    return conf


@pytest.fixture
def mongo(request, loop, mongo_conf):

    async def init_mogo(conf, loop):
        url = "mongodb://{}:{}".format(conf['host'], conf['port'])

        conn = aiomotor.AsyncIOMotorClient(
            url, max_pool_size=conf['max_pool_size'], io_loop=loop)
        await conn.open()
        return conn

    conn = loop.run_until_complete(init_mogo(mongo_conf, loop))

    def fin():
        conn.close()

    request.addfinalizer(fin)

    db = mongo_conf['database']
    return conn[db]
