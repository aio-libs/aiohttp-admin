import json
from collections.abc import Awaitable, Callable

from aiohttp.test_utils import TestClient

_Login = Callable[[TestClient], Awaitable[dict[str, str]]]


async def test_create_with_null(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_create"].url_for()
    p = {"data": json.dumps({"msg": None})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 200, await resp.text()
        assert await resp.json() == {"data": {"id": "4", "msg": None}}
