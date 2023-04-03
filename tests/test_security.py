import json
from typing import Awaitable, Callable, Optional
from unittest import mock

from aiohttp.test_utils import TestClient
from aiohttp_security import AbstractAuthorizationPolicy

from aiohttp_admin import Permissions, UserDetails

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


async def test_list_without_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                       login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {Permissions.edit, Permissions.delete}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_get_list"].url_for()
    p = {"pagination": json.dumps({"page": 1, "perPage": 10}),
         "sort": json.dumps({"field": "id", "order": "DESC"}), "filter": "{}"}
    h = await login(admin_client)
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 403
        # TODO(aiohttp-security05)
        # expected = "403: User does not have 'admin.dummy.view' permission"
        # assert await resp.text() == expected


async def test_get_resource_with_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                            login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.dummy.view"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_get_one"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"id": 1}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1}}


async def test_get_resource_with_wildcard_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                     login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.dummy.*"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_get_one"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"id": 1}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1}}


async def test_get_resource_with_negative_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                     login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.*", "~admin.dummy.*", "~admin.dummy2.add"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_get_one"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"id": 1}, headers=h) as resp:
        assert resp.status == 403
        # TODO(aiohttp-security05)
        # expected = "403: User does not have 'admin.dummy.view' permission"
        # assert await resp.text() == expected

    url = admin_client.app["admin"].router["dummy2_get_one"].url_for()
    async with admin_client.get(url, params={"id": 1}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1, "msg": "Test"}}

    url = admin_client.app["admin"].router["dummy2_create"].url_for()
    p = {"data": '{"msg": "Foo"}'}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 403
        # TODO(aiohttp-security05)
        # expected = "403: User does not have 'admin.dummy2.create' permission"


async def test_list_resource_finegrained_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                    login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.*", "~admin.dummy2.msg.view"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_list"].url_for()
    h = await login(admin_client)
    p = {"pagination": json.dumps({"page": 1, "perPage": 10}),
         "sort": json.dumps({"field": "id", "order": "DESC"}), "filter": "{}"}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 3}, {"id": 2}, {"id": 1}], "total": 3}


async def test_get_resource_finegrained_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                   login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.*", "~admin.dummy2.msg.view"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_one"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"id": 1}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1}}


async def test_get_many_resource_finegrained_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                        login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.*", "~admin.dummy2.msg.view"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_many"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"ids": "[1]"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 1}]}


async def test_create_resource_finegrained_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                      login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.*", "~admin.dummy2.msg.add"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_create"].url_for()
    h = await login(admin_client)
    p = {"data": json.dumps({"msg": "ABC"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 403
        # TODO(aiohttp-security05)
        # expected = "403: User does not have 'admin.dummy2.msg.create' permission"

    async with admin_client.post(url, params={"data": "{}"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 4, "msg": None}}


async def test_create_resource_filtered_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                   login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.*", "~admin.dummy2.msg.*"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_create"].url_for()
    h = await login(admin_client)
    p = {"data": json.dumps({"msg": "ABC"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 403
        # TODO(aiohttp-security05)
        # expected = "403: User does not have 'admin.dummy2.msg.create' permission"

    async with admin_client.post(url, params={"data": "{}"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 4}}


async def test_update_resource_finegrained_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                      login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.*", "~admin.dummy2.msg.edit"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update"].url_for()
    h = await login(admin_client)
    p = {"id": 1, "data": json.dumps({"id": 222, "msg": "ABC"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 222, "msg": "Test"}}


async def test_update_resource_filtered_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                   login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.*", "~admin.dummy2.msg.*"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update"].url_for()
    h = await login(admin_client)
    p = {"id": 1, "data": json.dumps({"id": 222, "msg": "ABC"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 222}}

    async with admin_client.app["db"]() as sess:
        r = await sess.get(admin_client.app["model2"], 1)
        assert r is None
        r = await sess.get(admin_client.app["model2"], 222)
        assert r.msg == "Test"


async def test_update_many_resource_finegrained_permission(  # type: ignore[no-any-unimported]
        create_admin_client: _CreateClient, login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.*", "~admin.dummy2.msg.edit"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update_many"].url_for()
    h = await login(admin_client)
    p = {"ids": "[1]", "data": json.dumps({"msg": "ABC"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 403
        # TODO(aiohttp-security05)
        # expected = "403: User does not have 'admin.dummy2.msg.edit' permission"


async def test_delete_resource_filtered_permission(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                   login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        assert identity == "admin"
        return {"permissions": {"admin.*", "~admin.dummy2.msg.view"}}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_delete"].url_for()
    h = await login(admin_client)
    p = {"id": 1, "previousData": "{}"}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1}}


async def test_permissions_cached(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                  login: _Login) -> None:
    identity_callback = mock.AsyncMock(spec_set=(), return_value={"permissions": {"admin.*"}})
    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_list"].url_for()
    h = await login(admin_client)
    identity_callback.assert_called_once()
    identity_callback.reset_mock()

    p = {"pagination": json.dumps({"page": 1, "perPage": 10}),
         "sort": json.dumps({"field": "id", "order": "DESC"}), "filter": "{}"}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200

    identity_callback.assert_called_once()


async def test_permission_filter_list(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                      login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.*|msg="Test"|msg="Foo"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    async with admin_client.app["db"].begin() as sess:
        sess.add(admin_client.app["model2"](msg="Foo"))

    url = admin_client.app["admin"].router["dummy2_get_list"].url_for()
    p = {"pagination": json.dumps({"page": 1, "perPage": 10}),
         "sort": json.dumps({"field": "id", "order": "DESC"}), "filter": "{}"}
    h = await login(admin_client)
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {
            "data": [{"id": 4, "msg": "Foo"}, {"id": 2, "msg": "Test"}, {"id": 1, "msg": "Test"}],
            "total": 3}


async def test_permission_filter_list2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                       login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.view|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_list"].url_for()
    p = {"pagination": json.dumps({"page": 1, "perPage": 10}),
         "sort": json.dumps({"field": "id", "order": "DESC"}), "filter": "{}"}
    h = await login(admin_client)
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {
            "data": [{"id": 2, "msg": "Test"}, {"id": 1, "msg": "Test"}], "total": 2}


async def test_permission_filter_get_one(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                         login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.*|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_one"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"id": 2}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 2, "msg": "Test"}}
    async with admin_client.get(url, params={"id": 3}, headers=h) as resp:
        assert resp.status == 403


async def test_permission_filter_get_one2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                          login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.view|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_one"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"id": 2}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 2, "msg": "Test"}}
    async with admin_client.get(url, params={"id": 3}, headers=h) as resp:
        assert resp.status == 403


async def test_permission_filter_get_many(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                          login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.*|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_many"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"ids": "[2, 3]"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 2, "msg": "Test"}]}
    async with admin_client.get(url, params={"ids": "[3]"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": []}


async def test_permission_filter_get_many2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                           login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.view|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_many"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"ids": "[2, 3]"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 2, "msg": "Test"}]}
    async with admin_client.get(url, params={"ids": "[3]"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": []}


async def test_permission_filter_create(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                        login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.*|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_create"].url_for()
    h = await login(admin_client)
    p = {"data": json.dumps({"msg": "Test"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 4, "msg": "Test"}}
    p = {"data": json.dumps({"msg": "Foo"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 403


async def test_permission_filter_create2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                         login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.add|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_create"].url_for()
    h = await login(admin_client)
    p = {"data": json.dumps({"msg": "Test"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 4, "msg": "Test"}}
    p = {"data": json.dumps({"msg": "Foo"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 403


async def test_permission_filter_update(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                        login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.*|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update"].url_for()
    h = await login(admin_client)
    p = {"id": 3, "data": json.dumps({"msg": "Test"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"id": 1, "data": json.dumps({"msg": "Foo"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"id": 1, "data": json.dumps({"msg": "Test"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200


async def test_permission_filter_update2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                         login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.edit|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update"].url_for()
    h = await login(admin_client)
    p = {"id": 3, "data": json.dumps({"msg": "Test"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"id": 1, "data": json.dumps({"msg": "Foo"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"id": 1, "data": json.dumps({"msg": "Test"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200


async def test_permission_filter_update_many(  # type: ignore[no-any-unimported]
    create_admin_client: _CreateClient, login: _Login
) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.*|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update_many"].url_for()
    h = await login(admin_client)
    p = {"ids": "[3]", "data": json.dumps({"msg": "Test"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"ids": "[1]", "data": json.dumps({"msg": "Foo"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"ids": "[1, 2]", "data": json.dumps({"msg": "Test"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200


async def test_permission_filter_update_many2(  # type: ignore[no-any-unimported]
    create_admin_client: _CreateClient, login: _Login
) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.edit|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update_many"].url_for()
    h = await login(admin_client)
    p = {"ids": "[3]", "data": json.dumps({"msg": "Test"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"ids": "[1]", "data": json.dumps({"msg": "Foo"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"ids": "[1, 2]", "data": json.dumps({"msg": "Test"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200


async def test_permission_filter_delete(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                        login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.*|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_delete"].url_for()
    h = await login(admin_client)
    p = {"id": 3, "previousData": "{}"}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"id": 1, "previousData": "{}"}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 200


async def test_permission_filter_delete2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                         login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.delete|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_delete"].url_for()
    h = await login(admin_client)
    p = {"id": 3, "previousData": "{}"}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"id": 1, "previousData": "{}"}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 200


async def test_permission_filter_delete_many(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                             login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.*|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_delete_many"].url_for()
    h = await login(admin_client)
    p = {"ids": "[2, 3]"}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"ids": "[3]"}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"ids": "[1, 2]"}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [1, 2]}


async def test_permission_filter_delete_many2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                              login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", 'admin.dummy2.delete|msg="Test"')}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_delete_many"].url_for()
    h = await login(admin_client)
    p = {"ids": "[2, 3]"}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"ids": "[3]"}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"ids": "[1, 2]"}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [1, 2]}


async def test_permission_filter_field_list(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                            login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.*|id=1|id=2")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_list"].url_for()
    p = {"pagination": json.dumps({"page": 1, "perPage": 10}),
         "sort": json.dumps({"field": "id", "order": "DESC"}), "filter": "{}"}
    h = await login(admin_client)
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {
            "data": [{"id": 3}, {"id": 2, "msg": "Test"}, {"id": 1, "msg": "Test"}], "total": 3}


async def test_permission_filter_field_list2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                             login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.view|id=1|id=3")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_list"].url_for()
    p = {"pagination": json.dumps({"page": 1, "perPage": 10}),
         "sort": json.dumps({"field": "id", "order": "DESC"}), "filter": "{}"}
    h = await login(admin_client)
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {
            "data": [{"id": 3, "msg": "Other"}, {"id": 2}, {"id": 1, "msg": "Test"}], "total": 3}


async def test_permission_filter_field_get_one(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                               login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.*|id=1|id=2")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_one"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"id": 1}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1, "msg": "Test"}}
    async with admin_client.get(url, params={"id": 3}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 3}}


async def test_permission_filter_field_get_one2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.view|id=1|id=2")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_one"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"id": 1}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1, "msg": "Test"}}
    async with admin_client.get(url, params={"id": 3}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 3}}


async def test_permission_filter_field_get_many(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.*|id=1|id=2")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_many"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"ids": "[2, 3]"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 2, "msg": "Test"}, {"id": 3}]}


async def test_permission_filter_field_get_many2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                                 login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.view|id=1|id=2")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_get_many"].url_for()
    h = await login(admin_client)
    async with admin_client.get(url, params={"ids": "[1, 3]"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 1, "msg": "Test"}, {"id": 3}]}


async def test_permission_filter_field_create(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                              login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.*|id=1|id=2")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_create"].url_for()
    h = await login(admin_client)
    p = {"data": json.dumps({"msg": "Spam"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 403
    async with admin_client.post(url, params={"data": "{}"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 4}}
    async with admin_client.app["db"]() as sess:
        r = await sess.get(admin_client.app["model2"], 4)
        assert r.msg is None


async def test_permission_filter_field_create2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                               login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.add|id=1|id=2")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_create"].url_for()
    h = await login(admin_client)
    p = {"data": json.dumps({"msg": "Spam"})}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 403
    async with admin_client.post(url, params={"data": "{}"}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 4, "msg": None}}
    async with admin_client.app["db"]() as sess:
        r = await sess.get(admin_client.app["model2"], 4)
        assert r.msg is None


async def test_permission_filter_field_update(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                              login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.*|id=1|id=2")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update"].url_for()
    h = await login(admin_client)
    p = {"id": 3, "data": json.dumps({"msg": "Spam"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 400
        assert await resp.text() == "400: No allowed fields to change."
    p = {"id": 1, "data": json.dumps({"msg": "Spam"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1, "msg": "Spam"}}
    p = {"id": 2, "data": json.dumps({"id": 5}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 5}}
    async with admin_client.app["db"]() as sess:
        r = await sess.get(admin_client.app["model2"], 2)
        assert r is None
        r = await sess.get(admin_client.app["model2"], 5)
        assert r.msg == "Test"


async def test_permission_filter_field_update2(create_admin_client: _CreateClient,  # type: ignore[no-any-unimported] # noqa: B950
                                               login: _Login) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.edit|id=1|id=2")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update"].url_for()
    h = await login(admin_client)
    p = {"id": 3, "data": json.dumps({"msg": "Spam"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 400
        assert await resp.text() == "400: No allowed fields to change."
    p = {"id": 1, "data": json.dumps({"msg": "Spam"}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1, "msg": "Spam"}}
    p = {"id": 2, "data": json.dumps({"id": 5}), "previousData": "{}"}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 5, "msg": "Test"}}
    async with admin_client.app["db"]() as sess:
        r = await sess.get(admin_client.app["model2"], 2)
        assert r is None
        r = await sess.get(admin_client.app["model2"], 5)
        assert r.msg == "Test"


async def test_permission_filter_field_update_many(  # type: ignore[no-any-unimported]
    create_admin_client: _CreateClient, login: _Login
) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.*|id=1|id=2")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update_many"].url_for()
    h = await login(admin_client)
    p = {"ids": "[3]", "data": json.dumps({"msg": "Spam"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"ids": "[1, 2]", "data": json.dumps({"msg": "Spam"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [1, 2]}


async def test_permission_filter_field_update_many2(  # type: ignore[no-any-unimported]
    create_admin_client: _CreateClient, login: _Login
) -> None:
    async def identity_callback(identity: Optional[str]) -> UserDetails:
        return {"permissions": ("admin.*", "admin.dummy2.msg.edit|id=1|id=2")}

    admin_client = await create_admin_client(identity_callback)

    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update_many"].url_for()
    h = await login(admin_client)
    p = {"ids": "[3]", "data": json.dumps({"msg": "Spam"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 403
    p = {"ids": "[1, 2]", "data": json.dumps({"msg": "Spam"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [1, 2]}
