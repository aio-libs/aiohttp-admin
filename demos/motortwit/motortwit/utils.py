import pytz
import os
import yaml
from hashlib import md5
from dateutil.parser import parse

import motor.motor_asyncio as aiomotor


def load_config(fname):
    with open(fname, 'rt') as f:
        data = yaml.load(f)
    # TODO: add config validation
    return data


async def init_mongo(conf, loop):
    host = os.environ.get('DOCKER_MACHINE_IP')
    conf['host'] = host
    mongo_uri = "mongodb://{}:{}".format(conf['host'], conf['port'])
    conn = aiomotor.AsyncIOMotorClient(
        mongo_uri,
        max_pool_size=conf['max_pool_size'],
        io_loop=loop)
    await conn.open()
    db_name = conf['database']
    return conn[db_name]


def robo_avatar_url(email, size=80):
    """Return the gravatar image for the given email address."""
    hash = md5(email.strip().lower().encode('utf-8')).hexdigest()
    url = "https://robohash.org/{hash}.png?size={size}x{size}".format(
        hash=hash, size=size)
    return url


def format_datetime(timestamp):
    if isinstance(timestamp, str):
        timestamp = parse(timestamp)
    return timestamp.replace(tzinfo=pytz.utc).strftime('%Y-%m-%d @ %H:%M')


def redirect(request, name, **kw):
    router = request.app.router
    location = router[name].url(**kw)
    return web.HTTPFound(location=location)
