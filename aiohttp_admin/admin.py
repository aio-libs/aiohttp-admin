from aiohttp_jinja2 import render_template
from yarl import URL

from .consts import TEMPLATE_APP_KEY, APP_KEY


__all__ = ['Admin', 'get_admin']


def get_admin(app, *, app_key=APP_KEY):
    return app.get(app_key)


class Admin:

    def __init__(self, app, *, name=None, url=None, template=None, loop):
        self._app = app
        self._loop = loop
        self._resources = []
        # TODO: check that url starts with /
        self._url = URL(url or '/admin')
        self._name = name or 'aiohttp_admin'
        self._temalate = template or 'admin.html'

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
