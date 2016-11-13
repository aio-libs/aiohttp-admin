from aiohttp_jinja2 import render_template
from aiohttp_security import remember, forget
from yarl import URL

from .consts import TEMPLATE_APP_KEY
from .exceptions import JsonValidaitonError
from .security import authorize
from .utils import json_response, validate_payload, LoginForm


__all__ = ['AdminHandler', 'setup_admin_handlers']


class AdminHandler:

    def __init__(self, admin, *, resources, name=None, template=None, loop):
        self._admin = admin
        self._loop = loop
        self._name = name or 'aiohttp_admin'
        self._temalate = template or 'admin.html'
        self._login_template = 'login.html'

        for r in resources:
            r.setup(self._admin, URL('/'))
        self._resources = tuple(resources)

    @property
    def template(self):
        return self._temalate

    @property
    def name(self):
        return self._name

    @property
    def resources(self):
        return self._resources

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
        if "Authorization" not in request.headers:
            msg = "Auth header is not present, can not destroy token"
            raise JsonValidaitonError(msg)
        router = request.app.router
        location = router["admin.login"].url()
        payload = {"location": location}
        response = json_response(payload)
        await forget(request, response)
        return response


def setup_admin_handlers(admin, admin_handler, static_folder, admin_conf_path):
    add_route = admin.router.add_route
    add_static = admin.router.add_static
    a = admin_handler
    add_route('GET', '', a.index_page, name='admin.index')
    add_route('GET', '/login', a.login_page, name='admin.login')
    add_route('POST', '/token', a.token, name='admin.token')
    add_route('DELETE', '/logout', a.logout, name='admin.logout')
    add_static('/static', path=static_folder, name='admin.static')
    add_static('/config', path=admin_conf_path, name='admin.config')
