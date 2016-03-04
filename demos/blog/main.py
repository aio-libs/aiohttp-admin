import asyncio
import logging
import pathlib
import yaml
import aiopg.sa

import aiohttp_jinja2
import jinja2
from aiohttp import web

import aiohttp_admin
from aiohttp_admin.backends.sa import SAResource
import db

PROJ_ROOT = pathlib.Path(__file__).parent.parent
TEMPLATES_ROOT = pathlib.Path(__file__).parent / 'templates'


class SiteHandler:

    def __init__(self, pg):
        self.pg = pg

    @aiohttp_jinja2.template('index.html')
    async def index(self, request):
        return {}


def setup_admin(app, pg, admin_config_path):
    admin = aiohttp_admin.setup(app, admin_config_path)

    admin.add_resource(SAResource(pg, db.post, url='posts'))
    admin.add_resource(SAResource(pg, db.tag, url='tags'))
    admin.add_resource(SAResource(pg, db.comment, url='comments'))
    admin.add_static()
    return admin


async def setup_pg(app, conf, loop):
    # create connection to the database
    pg = await init_postgres(conf['postgres'], loop)

    async def close_pg(app):
        pg.close()
        await pg.wait_closed()

    app.on_cleanup.append(close_pg)
    return pg


async def init(loop):
    # load config from yaml file
    conf = load_config(str(PROJ_ROOT / 'config' / 'dev.yaml'))

    # setup application and extensions
    app = web.Application(loop=loop)
    pg = await setup_pg(app, conf, loop)

    # init modules
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(str(TEMPLATES_ROOT)))
    admin_config = str(PROJ_ROOT / 'static' / 'js')
    # setup_admin(app, pg, admin_config)
    setup_admin(app, pg, None)

    # setup views and routes
    handler = SiteHandler(pg)
    add_route = app.router.add_route
    add_route('GET', '/', handler.index)
    app.router.add_static('/static', path=str(PROJ_ROOT / 'static'))

    host, port = conf['host'], conf['port']
    return app, host, port


def load_config(fname):
    with open(fname, 'rt') as f:
        data = yaml.load(f)
    # TODO: add config validation
    return data


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


def main():
    # init logging
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    app, host, port = loop.run_until_complete(init(loop))
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    main()
