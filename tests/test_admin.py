import aiohttp_admin
from aiohttp import web


def test_get_admin(loop):
    app = web.Application(loop=loop)
    resources = tuple()
    admin = aiohttp_admin.setup(app, './', resources=resources)

    fetched_admin = aiohttp_admin.get_admin(app)
    assert admin is fetched_admin


def test_get_admin_with_app_key(loop):
    app = web.Application(loop=loop)
    app_key = 'other_place'
    resources = tuple()
    admin = aiohttp_admin.setup(app, './', resources=resources,
                                app_key=app_key)

    fetched_admin = aiohttp_admin.get_admin(app, app_key=app_key)
    assert admin is fetched_admin


def test_admin_default_ctor(loop):
    app = web.Application(loop=loop)
    admin = aiohttp_admin.AdminHandler(app, loop=loop)
    assert admin.name == 'aiohttp_admin'
    assert admin.template == 'admin.html'


def test_admin_ctor(loop):
    app = web.Application(loop=loop)
    name = 'custom admin name'
    template = 'other.html'
    admin = aiohttp_admin.AdminHandler(app, name=name, template=template,
                                       loop=loop)
    assert name == admin.name
    assert template == admin.template
