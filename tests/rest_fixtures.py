import json

import aiohttp
import pytest
from aiohttp import web
from yarl import URL

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

    def __init__(self, url, *, admin_prefix=None, headers=None, loop):
        self._loop = loop
        self._url = URL(url)
        self._admin_prefix = admin_prefix or 'admin'
        self._session = aiohttp.ClientSession(loop=loop)
        self._headers = headers or {}

    RestClientError = RestClientError
    JsonRestError = JsonRestError

    @property
    def base_url(self):
        return self._url

    @property
    def admin_prefix(self):
        return self._admin_prefix

    async def request(self, method, path, data=None, params=None,
                      headers=None, json_dumps=True, token=None,
                      **kwargs):
        url = self._url / path
        if json_dumps and (data is not None):
            data = jsonify(data).encode('utf-8')

        h = self._headers.copy()
        if headers:
            h.update(headers)
        if token:
            h.update({"Authorization": token})
        resp = await self._session.request(method, str(url),
                                           params=params, data=data,
                                           headers=h, **kwargs)
        return resp

    async def handle_response(self, resp):
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
        # TODO: make coroutine
        if self._session:
            self._session.close()

    def set_token(self, token):
        self._headers["Authorization"] = token

    async def create(self, resource, data, **kw):
        url = '{}/{}'.format(self._admin_prefix, resource)
        resp = await self.request("POST", url, data=data, **kw)
        answer = await self.handle_response(resp)
        return answer

    async def detail(self, resource, entity_id, **kw):
        path = '{}/{}/{}'.format(self._admin_prefix, resource, entity_id)
        resp = await self.request("GET", path, **kw)
        answer = await self.handle_response(resp)
        return answer

    async def list(self, resource, page=1, per_page=30, sort_field=None,
                   sort_dir=None, filters=None, **kw):
        url = '{}/{}'.format(self._admin_prefix, resource)
        f = json.dumps(filters or {})

        query = {'_page': page, '_perPage': per_page, '_filters': f}

        sort_field and query.update({'_sortField': sort_field})
        sort_dir and query.update({'_sortDir': sort_dir})

        resp = await self.request("GET", url, params=query, **kw)
        answer = await self.handle_response(resp)
        return answer

    async def update(self, resource, entity_id, data, **kw):
        path = '{}/{}/{}'.format(self._admin_prefix, resource, entity_id)
        resp = await self.request("PUT", path, data=data, **kw)
        answer = await self.handle_response(resp)
        return answer

    async def delete(self, resource, entity_id, **kw):
        path = '{}/{}/{}'.format(self._admin_prefix, resource, entity_id)
        resp = await self.request("DELETE", path, **kw)
        answer = await self.handle_response(resp)
        return answer

    async def token(self, username, password):
        path = '{}/{}'.format(self._admin_prefix, 'token')
        data = dict(username=username, password=password)
        resp = await self.request("POST", path, data=data)
        token = resp.headers.get('X-Token')
        await self.handle_response(resp)
        return token

    async def destroy_token(self, token):
        path = '{}/{}'.format(self._admin_prefix, 'logout')
        h = {'Authorization': token}
        resp = await self.request("DELETE", path, headers=h)
        await self.handle_response(resp)
        return token


@pytest.yield_fixture
def create_server(loop, unused_port):
    cleanup = []

    async def create(*, debug=False, ssl_ctx=None, proto='http'):
        app = web.Application(loop=loop, debug=debug)
        port = unused_port()
        if ssl_ctx:
            proto += 's'
        url = "{}://127.0.0.1:{}".format(proto, port)

        async def app_starter():
            handler = app.make_handler(keep_alive_on=False)
            srv = await loop.create_server(handler, '127.0.0.1', port,
                                           ssl=ssl_ctx)
            cleanup.append((app, handler, srv))
            return

        return app, url, app_starter

    yield create

    async def finish():
        for app, handler, srv in cleanup:
            if app is None:
                continue
            await handler.finish_connections()
            # await app.finish()
            srv.close()
            await srv.wait_closed()

    loop.run_until_complete(finish())


@pytest.yield_fixture
def create_app_and_client(create_server, loop):
    client = None

    async def maker(*, server_params=None, client_params=None):
        nonlocal client
        if server_params is None:
            server_params = {}
        server_params.setdefault('debug', False)
        server_params.setdefault('ssl_ctx', None)
        app, url, app_starter = await create_server(**server_params)
        if client_params is None:
            client_params = {}
        client = AdminRESTClient(url, **client_params, loop=loop)
        return app, client, app_starter

    yield maker
    if client is not None:
        client.close()
