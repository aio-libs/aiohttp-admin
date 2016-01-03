import asyncio
import pathlib

import aiohttp_admin
from aiohttp import web


# custom admin views
class FirstView(aiohttp_admin.BaseView):

    async def first(self, request):
        return self.render(request, 'first.html', msg='Default view')

    async def second(self, request):
        return self.render(request, 'first.html', msg='Other view')

    def urls(self):
        return [('GET', '/', self.first, 'v1'),
                ('GET', '/v1', self.second, 'v2')]


class SecondView(aiohttp_admin.BaseView):

    async def first(self, request):
        return self.render(request, 'second.html', msg='Default view')

    async def second(self, request):
        return self.render(request, 'second.html', msg='Other view')

    def urls(self):
        return [('GET', '/', self.first, 'v1'),
                ('GET', '/v2', self.second, 'v2')]


# main project views
class SiteHandler:

    def index(self, request):
        t = 'To access admin views go to http://localhost:9000/admin/'
        return web.Response(text=t)


def setup_routes(app, handler):
    add_route = app.router.add_route
    add_route('GET', '/', handler.index)


PROJ_ROOT = pathlib.Path(__file__).resolve().parent
TEMPLATES_ROOT = PROJ_ROOT / 'templates'


def setup_admin(app):
    template_folder = str(TEMPLATES_ROOT)
    admin = aiohttp_admin.setup(app=app, template_folder=template_folder)
    admin.add_view(FirstView(name='First View', url='first'))
    admin.add_view(SecondView(name='Second View', url='second'))


async def init(loop):
    app = web.Application(loop=loop)
    # register custom templates to admin
    setup_admin(app)
    handler = SiteHandler()
    setup_routes(app, handler)

    app_handler = app.make_handler()
    host, port = '127.0.0.1', 9000
    srv = await loop.create_server(app_handler, host, port)
    print("Server started at http://{0}:{1}".format(host, port))
    return srv, app_handler


loop = asyncio.get_event_loop()
srv, app_handler = loop.run_until_complete(init(loop))

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    loop.run_until_complete(app_handler.finish_connections())
    srv.close()
    loop.run_until_complete(srv.wait_closed())
loop.close()
