import asyncio
import logging
import pathlib

import aiohttp_jinja2
import jinja2
from aiohttp import web

import aiohttp_admin
import aiohttp_security

from motortwit import db
from motortwit.routes import setup_routes
from motortwit.views import SiteHandler
from motortwit.utils import (load_config, init_mongo, robo_avatar_url,
                             format_datetime)
from aiohttp_session import session_middleware
from aiohttp_session import SimpleCookieStorage
from aiohttp_admin.backends.mongo import MotorResource
from aiohttp_admin.security import DummyAuthPolicy, DummyTokenIdentityPolicy


PROJ_ROOT = pathlib.Path(__file__).parent.parent
TEMPLATES_ROOT = pathlib.Path(__file__).parent / 'templates'


def setup_admin(app, mongo):
    admin_config_path = str(PROJ_ROOT / 'static' / 'js')
    m = mongo
    resources = (MotorResource(m.user, db.user, url="user"),
                 MotorResource(m.message, db.message, url="message"),
                 MotorResource(m.follower, db.follower, url="follower"))
    admin = aiohttp_admin.setup(app, admin_config_path, resources=resources)

    # setup dummy auth and identity
    ident_policy = DummyTokenIdentityPolicy()
    auth_policy = DummyAuthPolicy(username="admin", password="admin")
    aiohttp_security.setup(admin, ident_policy, auth_policy)
    return admin


async def setup_mongo(app, conf, loop):
    mongo = await init_mongo(conf['mongo'], loop)

    async def close_mongo(app):
        mongo.client.close()

    app.on_cleanup.append(close_mongo)
    return mongo


def setup_jinja(app):
    jinja_env = aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(str(TEMPLATES_ROOT)))

    jinja_env.filters['datetimeformat'] = format_datetime
    jinja_env.filters['robo_avatar_url'] = robo_avatar_url


async def init(loop):
    conf = load_config(str(PROJ_ROOT / 'config' / 'config.yml'))

    app = web.Application(loop=loop)
    cookie_storage = SimpleCookieStorage()
    app = web.Application(middlewares=[session_middleware(cookie_storage)])
    mongo = await setup_mongo(app, conf, loop)

    setup_jinja(app)

    admin = setup_admin(app, mongo)
    app.router.add_subapp('/admin', admin)

    app.router.add_static('/static', path=str(PROJ_ROOT / 'static'))

    # setup views and routes
    handler = SiteHandler(mongo)
    setup_routes(app, handler, PROJ_ROOT)

    host, port = conf['host'], conf['port']
    return app, host, port


def main():
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    app, host, port = loop.run_until_complete(init(loop))
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    main()
