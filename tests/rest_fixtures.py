import json

import aiohttp
from aiohttp import web
import pytest

from aiohttp_admin.utils import jsonify


class RestClientError(Exception):
    """Base exception class for RESTClient"""

    @property
    def status_code(self):
        return self.args[0]


class PlainRestError(RestClientError):
    """Answer is not JSON, for example for 500 Internal Server Error"""

    @property
    def error_text(self):
        return self.args[1]


class JsonRestError(RestClientError):
    """Answer is JSON error report"""

    @property
    def error_json(self):
        return self.args[1]


class AdminRESTClient:

    def __init__(self, url, *, admin_prefix=None, loop):
        self._loop = loop
        self._url = url
        self._admin_prefix = admin_prefix or 'admin'
        self._session = aiohttp.ClientSession(loop=loop)

    async def request(self, method, path, data=None, params=None,
                      headers=None, json_dumps=True):
        if json_dumps and (data is not None):
            data = jsonify(data).encode('utf-8')
        url = '{}/{}/{}'.format(self._url, self._admin_prefix, path)
        resp = await self._session.request(method, url,
                                           params=params, data=data,
                                           headers=headers)
        body = await resp.read()
        if resp.status in (200, 201):
            jsoned = await resp.json()
            return jsoned
        elif resp.status == 500:
            raise PlainRestError(body.decode('utf-8'))
        else:
            try:
                jsoned = await resp.json(encoding='utf-8')
            except ValueError:
                raise PlainRestError(body.decode('utf-8'))
            else:
                raise JsonRestError(resp.status, jsoned)

    def close(self):
        if self._session:
            self._session.close()

    async def create(self, resource, data):
        answer = await self.request("POST", resource, data=data)
        return answer

    async def detail(self, resource, entity_id):
        path = '{}/{}'.format(resource, entity_id)
        answer = await self.request("GET", path)
        return answer

    async def list(self, resource, page=1, per_page=30, sort_field='id',
                   sort_dir='DESC', filters=None):
        f = json.dumps(filters or {})
        query = {'_page': page,
                 '_perPage': per_page,
                 '_sortField': sort_field,
                 '_sortDir': sort_dir,
                 '_filters': f}
        answer = await self.request("GET", resource, params=query)
        return answer

    async def update(self, resource, entity_id, data):
        path = '{}/{}'.format(resource, entity_id)
        answer = await self.request("PUT", path, data=data)
        return answer

    async def delete(self, resource, entity_id):
        path = '{}/{}'.format(resource, entity_id)
        answer = await self.request("DELETE", path)
        return answer


@pytest.yield_fixture
def create_server(loop, unused_port):
    app = handler = srv = None

    async def create(*, debug=False, ssl_ctx=None, proto='http'):
        nonlocal app, handler, srv
        app = web.Application(loop=loop)
        port = unused_port()
        handler = app.make_handler(debug=debug, keep_alive_on=False)
        srv = await loop.create_server(handler, '127.0.0.1', port, ssl=ssl_ctx)
        if ssl_ctx:
            proto += 's'
        url = "{}://127.0.0.1:{}".format(proto, port)
        return app, url

    yield create


@pytest.yield_fixture
def create_app_and_client(create_server, loop):
    client = None

    async def maker(*, server_params=None, client_params=None):
        nonlocal client
        if server_params is None:
            server_params = {}
        server_params.setdefault('debug', False)
        server_params.setdefault('ssl_ctx', None)
        app, url = await create_server(**server_params)
        if client_params is None:
            client_params = {}
        # TODO: pass client_params here
        client = AdminRESTClient(url, loop=loop)
        return app, client

    yield maker
    client.close()
