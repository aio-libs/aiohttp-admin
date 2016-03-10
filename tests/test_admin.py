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


def test_admin_default_ctor(loop):
    app = web.Application(loop=loop)
    admin = aiohttp_admin.Admin(app, loop=loop)
    assert app is admin.app
    assert 'aiohttp_admin' == admin.name
    assert 'admin.html' == admin.template


def test_admin_ctor(loop):
    app = web.Application(loop=loop)
    name = 'custom admin name'
    template = 'other.html'
    admin = aiohttp_admin.Admin(app, name=name, template=template, loop=loop)
    assert app is admin.app
    assert name == admin.name
    assert template == admin.template
