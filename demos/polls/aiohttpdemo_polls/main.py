import asyncio
import logging
import pathlib

import aiohttp_admin
import aiohttp_jinja2
import aiohttp_security
import jinja2

from aiohttp import web
from aiohttp_admin.backends.sa import PGResource
from aiohttp_admin.security import DummyAuthPolicy, DummyTokenIdentityPolicy

import aiohttpdemo_polls.db as db
from aiohttpdemo_polls.routes import setup_routes
from aiohttpdemo_polls.utils import init_postgres, load_config
from aiohttpdemo_polls.views import SiteHandler


PROJ_ROOT = pathlib.Path(__file__).parent.parent
TEMPLATES_ROOT = pathlib.Path(__file__).parent / 'templates'


def setup_admin(app, pg, admin_config_path):
    admin_config_path = str(PROJ_ROOT / 'static' / 'js')
    resources = (PGResource(pg, db.question, url='question'),
                 PGResource(pg, db.choice, url='choice'))
    admin = aiohttp_admin.setup(app, admin_config_path, resources=resources)

    # setup dummy auth and identity
    ident_policy = DummyTokenIdentityPolicy()
    auth_policy = DummyAuthPolicy(username="admin", password="admin")
    aiohttp_security.setup(admin, ident_policy, auth_policy)
    return admin


async def init(loop):
    # setup application and extensions
    app = web.Application(loop=loop)
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(str(TEMPLATES_ROOT)))
    # load config from yaml file
    conf = load_config(str(PROJ_ROOT / 'config' / 'dev.yml'))

    # create connection to the database
    pg = await init_postgres(conf['postgres'], loop)

    async def close_pg(app):
        pg.close()
        await pg.wait_closed()

    # setup admin views
    admin_config = str(PROJ_ROOT / 'static' / 'js')
    admin = setup_admin(app, pg, admin_config)
    app.router.add_subapp('/admin', admin)

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
