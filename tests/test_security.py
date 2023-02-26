from enum import Enum
from typing import Awaitable, Callable, Optional, Union

from aiohttp.test_utils import TestClient
from aiohttp_security import AbstractAuthorizationPolicy

from aiohttp_admin import Permissions

_CreateClient = Callable[[AbstractAuthorizationPolicy], Awaitable[TestClient]]
_Login = Callable[[TestClient], Awaitable[dict[str, str]]]


async def test_no_token(admin_client: TestClient) -> None:
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_get_list"].url_for()
    async with admin_client.get(url) as resp:
        assert resp.status == 401
        assert await resp.text() == "401: Unauthorized"


async def test_invalid_token(admin_client: TestClient) -> None:
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_get_one"].url_for()
    h = {"Authorization": "invalid"}
    async with admin_client.get(url, headers=h) as resp:
        assert resp.status


async def test_valid_login_logout(admin_client: TestClient) -> None:
    assert admin_client.app
    url = admin_client.app["admin"].router["token"].url_for()
    login = {"username": "admin", "password": "admin123"}
    async with admin_client.post(url, json=login) as resp:
        assert resp.status == 200
        token = resp.headers["X-Token"]

    get_one_url = admin_client.app["admin"].router["dummy_get_one"].url_for()
    p = {"id": 1}
    h = {"Authorization": token}
    async with admin_client.get(get_one_url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1}}

    # Continue to test logout
    logout_url = admin_client.app["admin"].router["logout"].url_for()
    async with admin_client.delete(logout_url, headers=h) as resp:
        assert resp.status == 200

    async with admin_client.get(get_one_url, params=p, headers=h) as resp:
        assert resp.status == 401


async def test_missing_token(admin_client: TestClient) -> None:
    assert admin_client.app
    url = admin_client.app["admin"].router["token"].url_for()
    login = {"username": "admin", "password": "admin123"}
    async with admin_client.post(url, json=login) as resp:
        assert resp.status == 200

    cookies = tuple(admin_client.session.cookie_jar)
    assert len(cookies) == 1
    assert cookies[0]["path"] == "/admin"

    url = admin_client.app["admin"].router["dummy_get_one"].url_for()
    p = {"id": 1}
    async with admin_client.get(url, params=p) as resp:
        assert resp.status == 401


async def test_missing_cookie(admin_client: TestClient) -> None:
    assert admin_client.app
    url = admin_client.app["admin"].router["token"].url_for()
    login = {"username": "admin", "password": "admin123"}
    async with admin_client.post(url, json=login) as resp:
        assert resp.status == 200
        token = resp.headers["X-Token"]

    admin_client.session.cookie_jar.clear()

    url = admin_client.app["admin"].router["dummy_get_one"].url_for()
    p = {"id": 1}
    h = {"Authorization": token}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 401


async def test_login_invalid_payload(admin_client: TestClient) -> None:
    assert admin_client.app
    url = admin_client.app["admin"].router["token"].url_for()
    async with admin_client.post(url, json={"foo": "bar", "password": None}) as resp:
        assert resp.status == 400
        assert await resp.json() == [{
            "loc": ["__root__", "username"],
            "msg": "field required",
            "type": "value_error.missing"
        }, {
            "loc": ["__root__", "password"],
            "msg": "none is not an allowed value",
            "type": "type_error.none.not_allowed"
        }]


async def test_list_without_permisson(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                      login: _Login) -> None:
    class AuthPolicy(AbstractAuthorizationPolicy):  # type: ignore[misc,no-any-unimported]
        async def authorized_userid(self, identity: str) -> Optional[str]:
            return identity if identity == "admin" else None

        async def permits(self, identity: Optional[str], permission: Union[str, Enum],
                          context: object = None) -> bool:
            return identity == "admin" and permission in {Permissions.edit, Permissions.delete}

    admin_client = await create_admin_client(AuthPolicy())

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_get_list"].url_for()
    p = {"page": 1, "pagination": 10}
    h = await login(admin_client)
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 403
        # TODO
        # expected = "User does not have '{}' permission".format(Permissions.view)
        # assert await resp.text() == expected
