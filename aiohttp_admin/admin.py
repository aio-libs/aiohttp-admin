import aiohttp_jinja2

from .consts import TEMPLATE_APP_KEY, APP_KEY


__all__ = ['Admin', 'get_admin']


def get_admin(app, *, app_key=APP_KEY):
    return app.get(app_key)


class Admin:

    def __init__(self, app, *, name=None, url=None, loop):
        self._app = app
        self._loop = loop
        self._resources = []
        self._url = url or '/admin'
        self._name = name or 'aiohttp_admin'
        self._entities = []

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

    @aiohttp_jinja2.template('config.js', app_key=TEMPLATE_APP_KEY)
    async def config_handler(self, request):
        print('render config.js')
        print(self._resources)
        print(self._entities)
        return {'name': self._name, 'entities': self._entities}

    def add_static(self):
        for resource in self._resources:
            self._entities.append({
                'url': resource.url,
                'name': resource.table.name
            })
