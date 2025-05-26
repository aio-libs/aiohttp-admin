import json
from collections.abc import Awaitable, Callable

from aiohttp import web
from aiohttp.test_utils import TestClient

from conftest import admin

_Client = TestClient[web.Request, web.Application]
_Login = Callable[[_Client], Awaitable[dict[str, str]]]


async def test_create_with_null(admin_client: _Client, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app[admin].router["dummy2_create"].url_for()
    p = {"data": json.dumps({"data": {"msg": None}})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 200, await resp.text()
        assert await resp.json() == {"data": {"id": "4", "data": {"id": 4, "msg": None}}}


async def test_invalid_field(admin_client: _Client, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app[admin].router["dummy2_create"].url_for()
    p = {"data": json.dumps({"data": {"incorrect": "foo"}})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 400, await resp.text()
        assert "Invalid field 'incorrect'" in await resp.text()
