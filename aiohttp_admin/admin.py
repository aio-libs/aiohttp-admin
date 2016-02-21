import aiohttp_jinja2

from .consts import TEMPLATE_APP_KEY, APP_KEY


__all__ = ['Admin', 'admin_middleware_factory']


async def admin_middleware_factory(app, handler):
    async def admin_middleware(request):
        try:
            response = await handler(request)
        except Exception as e:
            raise e
        return response

    return admin_middleware


def get_admin(app, *, app_key=APP_KEY):
    return app.get(app_key)


class Admin:

    def __init__(self, app, *, name=None, url=None, loop):
        self._app = app
        self._loop = loop
        self._resources = []
        self._url = url or '/admin'
        self._name = name or 'aiohttp_admin'

    @property
    def app(self):
        return self._app

    @property
    def name(self):
        return self._name

    def add_resource(self, resource):
        resource.setup(self.app, self._url)
        self._resources.append(resource)

    @aiohttp_jinja2.template('admin.html', app_key=TEMPLATE_APP_KEY)
    async def index_handler(self, request):
        return {'name': self._name}
