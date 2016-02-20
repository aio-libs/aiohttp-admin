import asyncio
import logging
import pathlib

import aiohttp_jinja2
import jinja2
from aiohttp import web

import aiohttpdemo_polls.db as db
from aiohttpdemo_polls.routes import setup_routes
from aiohttpdemo_polls.utils import init_postgres, load_config
from aiohttpdemo_polls.views import SiteHandler

import aiohttp_admin
from aiohttp_admin.backends.sa import SAResource


PROJ_ROOT = pathlib.Path(__file__).parent.parent
TEMPLATES_ROOT = pathlib.Path(__file__).parent / 'templates'


def setup_admin(app, pg, admin_config_path):
    admin = aiohttp_admin.setup(app, admin_config_path)

    admin.add_resource(SAResource(pg, db.question, url='question'))
    admin.add_resource(SAResource(pg, db.choice, url='choice'))
    return admin


async def init(loop):
    # setup application and extensions
    app = web.Application(loop=loop)
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(str(TEMPLATES_ROOT)))
    # load config from yaml file
    conf = load_config(str(PROJ_ROOT / 'config' / 'polls.yaml'))

    # create connection to the database
    pg = await init_postgres(conf['postgres'], loop)

    async def close_pg(app):
        pg.close()
        await pg.wait_closed()

    # setup admin views
    admin_config = str(PROJ_ROOT / 'static' / 'js')
    setup_admin(app, pg, admin_config)

    app.on_cleanup.append(close_pg)

    # setup views and routes
    handler = SiteHandler(pg)
    setup_routes(app, handler, PROJ_ROOT)

    host, port = conf['host'], conf['port']
    return app, host, port


def main():
    # init logging
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    app, host, port = loop.run_until_complete(init(loop))
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    main()
