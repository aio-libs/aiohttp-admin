import os

import aiopg.sa
import yaml


def load_config(fname):
    with open(fname, 'rt') as f:
        data = yaml.load(f)
    # TODO: add config validation
    return data


async def init_postgres(conf, loop):
    host = os.environ.get('DOCKER_MACHINE_IP', '127.0.0.1')
    conf['host'] = host
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
