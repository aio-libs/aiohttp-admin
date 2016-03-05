import aiohttp_admin
from aiohttp import web


def test_get_admin(loop):
    app = web.Application(loop=loop)
    admin = aiohttp_admin.setup(app, './')

    fetched_admin = aiohttp_admin.get_admin(app)
    assert admin is fetched_admin


def test_get_admin_with_app_key(loop):
    app = web.Application(loop=loop)
    app_key = 'other_place'
    admin = aiohttp_admin.setup(app, './', app_key=app_key)

    fetched_admin = aiohttp_admin.get_admin(app, app_key=app_key)
    assert admin is fetched_admin
