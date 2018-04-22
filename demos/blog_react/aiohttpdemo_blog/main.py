import asyncio
import logging
import pathlib

import jinja2
import aiohttp_jinja2
import aiohttp_security
from aiohttp import web
import aiohttp_admin

from aiohttpdemo_blog.utils import init_postgres, load_config
from aiohttp_admin.security import DummyAuthPolicy, DummyTokenIdentityPolicy
from .admin import schema


PROJ_ROOT = pathlib.Path(__file__).parent.parent
TEMPLATES_ROOT = pathlib.Path(__file__).parent / 'templates'


class SiteHandler:

    def __init__(self, pg):
        self.pg = pg

    @aiohttp_jinja2.template('index.html')
    async def index(self, _):
        return {}


def setup_admin(app, pg):
    admin = aiohttp_admin._setup(
        app,
        title='Blog admin',
        schema=schema,
        db=pg,
    )

    # setup dummy auth and identity
    ident_policy = DummyTokenIdentityPolicy()
    auth_policy = DummyAuthPolicy(username="admin", password="admin")
    aiohttp_security.setup(admin, ident_policy, auth_policy)

    app.add_subapp('/admin/', admin)


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
    conf = load_config(str(PROJ_ROOT / 'config' / 'dev.yml'))

    # setup application and extensions
    app = web.Application(loop=loop)
    pg = await setup_pg(app, conf, loop)

    # init modules
    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(str(TEMPLATES_ROOT))
    )

    setup_admin(app, pg)

    # setup views and routes
    handler = SiteHandler(pg)
    add_route = app.router.add_route
    add_route('GET', '/', handler.index)
    app.router.add_static('/static', path=str(PROJ_ROOT / 'static'))

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
