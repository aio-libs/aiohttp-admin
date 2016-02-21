import json

import aiohttp
import pytest


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

    def __init__(self, url, loop):
        self._loop = loop
        self._url = url
        self._session = aiohttp.ClientSession(loop=loop)

    async def request(self, method, path, data=None, params=None,
                      headers=None, json_dumps=True):
        if json_dumps and (data is not None):
            data = json.dumps(data).encode('utf-8')

        resp = await self._session.request(method, self._api_url + path,
                                           params=params, data=data,
                                           headers=headers,
                                           loop=self._loop)
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

    async def create(self, data):
        pass

    async def list(self, resource, offset, limit, filter):
        answer = await self.request("POST", resource)
        return answer

    async def update(self, data):
        pass

    async def delete(self, entity_id):
        pass


@pytest.fixture
def api(request, loop, base_url):
    client = AdminRESTClient(base_url, loop)

    def fin():
        client.close()

    request.addfinalizer(fin)
    return client
