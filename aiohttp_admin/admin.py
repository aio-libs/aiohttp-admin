from aiohttp_jinja2 import render_template
from aiohttp_security import remember, forget
from yarl import URL

from .consts import TEMPLATE_APP_KEY, APP_KEY
from .security import authorize
from .utils import json_response, validate_payload, LoginForm, redirect


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
        self._login_template = 'login.html'

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

    async def index_page(self, request):
        t = self._temalate
        context = {'name': self._name}
        return render_template(t, request, context, app_key=TEMPLATE_APP_KEY)

    async def login_page(self, request):
        t = self._login_template
        context = {}
        return render_template(t, request, context, app_key=TEMPLATE_APP_KEY)

    async def token(self, request):
        raw_payload = await request.read()
        data = validate_payload(raw_payload, LoginForm)
        await authorize(request, data['username'], data['password'])

        router = request.app.router
        location = router["admin.index"].url()
        payload = {"location": location}
        response = json_response(payload)
        await remember(request, response, data['username'])
        return response

    async def logout(self, request):
        response = redirect("admin.login")
        await forget(request, response)
        return response


def setup_admin_handlers(admin, url, static_url, static_folder,
                         admin_conf_path):
    add_route = admin.app.router.add_route
    add_static = admin.app.router.add_static
    a = admin
    add_route('GET', str(url), a.index_page, name='admin.index')
    add_route('GET', str(url / 'login'), a.login_page, name='admin.login')
    add_route('POST', str(url / 'token'), a.token, name='admin.token')
    add_route('DELETE', str(url / 'logout'), a.logout, name='admin.logout')
    add_static(static_url, path=static_folder, name='admin.static')
    add_static('/admin/config', path=admin_conf_path, name='admin.config')
