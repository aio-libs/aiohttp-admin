from aiohttp_jinja2 import render_template

from .consts import TEMPLATE_APP_KEY, APP_KEY
from .backends.sa import PGResource
from .backends.sa_utils import build_sa_fe_field


__all__ = ['Admin', 'get_admin']


def get_admin(app, *, app_key=APP_KEY):
    return app.get(app_key)


class Admin:

    def __init__(self, app, *, name=None, url=None, template=None, loop):
        self._app = app
        self._loop = loop
        self._resources = []
        self._url = url or '/admin'
        self._name = name or 'aiohttp_admin'
        self._temalate = template or 'admin.html'
        self._config_template = 'config.js'
        self._entities = []

    @property
    def app(self):
        return self._app

    @property
    def template(self):
        return self._temalate

    @property
    def name(self):
        return self._name

    def add_resource(self, resource):
        resource.setup(self.app, self._url)
        self._resources.append(resource)

    async def index_handler(self, request):
        t = self._temalate
        context = {'name': self._name}
        return render_template(t, request, context, app_key=TEMPLATE_APP_KEY)

    async def config_handler(self, request):
        t = self._config_template
        context = {'name': self._name, 'entities': self._entities}
        return render_template(t, request, context, app_key=TEMPLATE_APP_KEY)

    def add_static(self):
        for resource in self._resources:
            data = {
                'url': resource.url,
                'name': resource.table_name,
            }
            if isinstance(resource, PGResource):
                mapper = build_sa_fe_field
            data.setdefault(
                'columns', [
                    (title, mapper(column.type))
                    for title, column in resource.columns
                ]
            )

            self._entities.append(data)