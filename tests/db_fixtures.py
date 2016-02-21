import pytest
import aiopg.sa
import motor.motor_asyncio as aiomotor


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
