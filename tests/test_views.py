import json
import re
from typing import Awaitable, Callable

import sqlalchemy as sa
from aiohttp.test_utils import TestClient

_Login = Callable[[TestClient], Awaitable[dict[str, str]]]


async def test_admin_view(admin_client: TestClient) -> None:
    assert admin_client.app
    url = admin_client.app["admin"].router["index"].url_for()
    async with admin_client.get(url) as resp:
        assert resp.status == 200
        html = await resp.text()

    m = re.search("<title>(.*)</title>", html)
    assert m is not None
    assert m.group(1) == "My Admin"

    m = re.search('<script src="(.*)" defer="defer"></script>', html)
    assert m is not None
    assert m.group(1) == "/admin/static/admin.js"

    m = re.search("<body data-state='(.*)'>", html)
    assert m is not None
    state = json.loads(m.group(1))

    r = state["resources"]["dummy"]
    assert r["list_omit"] == []
    assert r["fields"] == {"id": {"type": "NumberField", "props": {"alwaysOn": "alwaysOn"}}}
    assert r["inputs"] == {"id": {"type": "NumberInput", "props": {"alwaysOn": "alwaysOn"},
                                  "show_create": False, "validators": [["required"]]}}
    assert r["repr"] == "id"
    assert state["urls"] == {"token": "/admin/token", "logout": "/admin/logout"}


async def test_list_pagination(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    async with admin_client.app["db"].begin() as sess:
        for _ in range(25):
            sess.add(admin_client.app["model"]())

    url = admin_client.app["admin"].router["dummy_get_list"].url_for()
    p = {"pagination": '{"page": 1, "perPage": 30}',
         "sort": '{"field": "id", "order": "ASC"}', "filter": '{}'}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        all_rows = await resp.json()
        assert len(all_rows["data"]) == all_rows["total"] == 26
        assert tuple(r["id"] for r in all_rows["data"]) == tuple(range(1, 27))

    p = {"pagination": '{"page": 2, "perPage": 12}',
         "sort": '{"field": "id", "order": "DESC"}', "filter": '{}'}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        page = await resp.json()
        assert page["total"] == 26
        assert tuple(r["id"] for r in page["data"]) == tuple(range(14, 2, -1))

    p = {"pagination": '{"page": 20, "perPage": 10}',
         "sort": '{"field": "id", "order": "DESC"}', "filter": '{}'}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        page = await resp.json()
        assert page["data"] == []
        assert page["total"] == 26


async def test_list_filtering_by_pk(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    async with admin_client.app["db"].begin() as sess:
        for _ in range(15):
            sess.add(admin_client.app["model"]())

    url = admin_client.app["admin"].router["dummy_get_list"].url_for()
    p = {"pagination": '{"page": 1, "perPage": 10}',
         "sort": '{"field": "id", "order": "ASC"}', "filter": '{"id": 3}'}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 3}], "total": 1}


async def test_list_text_like_filtering(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    async with admin_client.app["db"].begin() as sess:
        for _ in range(15):
            sess.add(admin_client.app["model"]())

    url = admin_client.app["admin"].router["dummy_get_list"].url_for()
    p = {"pagination": '{"page": 1, "perPage": 10}',
         "sort": '{"field": "id", "order": "ASC"}', "filter": '{"id": "3"}'}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 3}, {"id": 13}], "total": 2}


async def test_get_one(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_get_one"].url_for()

    async with admin_client.get(url, params={"id": 1}, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1}}


async def test_get_one_not_exists(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_get_one"].url_for()

    async with admin_client.get(url, params={"id": 5}, headers=h) as resp:
        assert resp.status == 404


async def test_get_many(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    async with admin_client.app["db"].begin() as sess:
        for _ in range(15):
            sess.add(admin_client.app["model"]())

    url = admin_client.app["admin"].router["dummy_get_many"].url_for()
    p = {"ids": "[3, 7, 12]"}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 3}, {"id": 7}, {"id": 12}]}


async def test_get_many_not_exists(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    async with admin_client.app["db"].begin() as sess:
        for _ in range(5):
            sess.add(admin_client.app["model"]())

    url = admin_client.app["admin"].router["dummy_get_many"].url_for()
    p = {"ids": "[3, 4, 8]"}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [{"id": 3}, {"id": 4}]}

    p = {"ids": "[9, 10, 11]"}
    async with admin_client.get(url, params=p, headers=h) as resp:
        assert resp.status == 404


async def test_create(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_create"].url_for()
    p = {"data": "{}"}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 2}}

    async with admin_client.app["db"]() as sess:
        r = await sess.get(admin_client.app["model"], 2)
        assert r.id == 2


async def test_create_duplicate_id(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_create"].url_for()
    p = {"data": '{"id": 1}'}
    async with admin_client.post(url, params=p, headers=h) as resp:
        assert resp.status == 400


async def test_update(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_update"].url_for()
    p = {"id": 1, "data": '{"id": 4}', "previousData": '{"id": 1}'}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 4}}

    async with admin_client.app["db"]() as sess:
        r = await sess.get(admin_client.app["model"], 4)
        assert r.id == 4

        assert await sess.get(admin_client.app["model"], 1) is None
        assert await sess.get(admin_client.app["model"], 2) is None


async def test_update_deleted_entity(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_update"].url_for()
    p = {"id": 2, "data": '{"id": 4}', "previousData": '{"id": 2}'}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 404


async def test_update_invalid_attributes(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_update"].url_for()
    p = {"id": 1, "data": '{"id": 4, "foo": "invalid"}', "previousData": '{"id": 1}'}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 400
        assert "foo" in await resp.text()


async def test_update_many(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy2_update_many"].url_for()
    p = {"ids": "[1, 2]", "data": json.dumps({"msg": "ABC"})}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [1, 2]}

    async with admin_client.app["db"]() as sess:
        r = await sess.get(admin_client.app["model2"], 1)
        assert r.msg == "ABC"
        r = await sess.get(admin_client.app["model2"], 2)
        assert r.msg == "ABC"


async def test_update_many_deleted_entity(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_update_many"].url_for()
    p = {"ids": "[2]", "data": '{"id": 4}'}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 404


async def test_update_many_invalid_attributes(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_update_many"].url_for()
    p = {"ids": "[1]", "data": '{"foo": "invalid"}'}
    async with admin_client.put(url, params=p, headers=h) as resp:
        assert resp.status == 400
        assert "foo" in await resp.text()


async def test_delete(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_delete"].url_for()
    p = {"id": 1, "previousData": '{"id": 1}'}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": {"id": 1}}

    async with admin_client.app["db"]() as sess:
        assert await sess.get(admin_client.app["model"], 1) is None
        r = await sess.scalars(sa.select(admin_client.app["model"]))
        assert len(r.all()) == 0


async def test_delete_entity_not_exists(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    url = admin_client.app["admin"].router["dummy_delete"].url_for()
    p = {"id": 5, "previousData": '{"id": 5}'}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 404


async def test_delete_many(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    async with admin_client.app["db"].begin() as sess:
        for _ in range(5):
            sess.add(admin_client.app["model"]())

    url = admin_client.app["admin"].router["dummy_delete_many"].url_for()
    p = {"ids": '[2, 3, 5]'}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [2, 3, 5]}

    async with admin_client.app["db"]() as sess:
        r = await sess.scalars(sa.select(admin_client.app["model"]))
        models = r.all()
        assert len(models) == 3
        assert {m.id for m in models} == {1, 4, 6}


async def test_delete_many_not_exists(admin_client: TestClient, login: _Login) -> None:
    h = await login(admin_client)
    assert admin_client.app
    async with admin_client.app["db"].begin() as sess:
        for _ in range(5):
            sess.add(admin_client.app["model"]())

    url = admin_client.app["admin"].router["dummy_delete_many"].url_for()
    p = {"ids": '[2, 3, 9]'}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 200
        assert await resp.json() == {"data": [2, 3]}

    async with admin_client.app["db"]() as sess:
        r = await sess.scalars(sa.select(admin_client.app["model"]))
        models = r.all()
        assert len(models) == 4
        assert {m.id for m in models} == {1, 4, 5, 6}

    url = admin_client.app["admin"].router["dummy_delete_many"].url_for()
    p = {"ids": '[12, 13]'}
    async with admin_client.delete(url, params=p, headers=h) as resp:
        assert resp.status == 404

    async with admin_client.app["db"]() as sess:
        r = await sess.scalars(sa.select(admin_client.app["model"]))
        assert len(r.all()) == 4
