import pytest

from db_fixtures import ADMIN_TYPE_LIST


async def prepare_admin(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    num_entities = 10
    await create_entities(num_entities)
    return admin, client


@pytest.mark.parametrize('admin_type', ADMIN_TYPE_LIST)
@pytest.mark.run_loop
async def test_login_page(create_admin):
    _, client = await prepare_admin(create_admin)
    resp = await client.request('GET', 'admin/login')
    page = await resp.read()
    assert resp.status == 200
    assert b'username' in page


@pytest.mark.parametrize('admin_type', ADMIN_TYPE_LIST)
@pytest.mark.run_loop
async def test_admin_page_redirect(create_admin):
    _, client = await prepare_admin(create_admin)
    path = client.admin_prefix
    resp = await client.request('GET', path)
    page = await resp.read()
    assert resp.status == 200
    assert b"ng-admin" in page


@pytest.mark.parametrize('admin_type', ADMIN_TYPE_LIST)
@pytest.mark.run_loop
async def test_token(create_admin):
    _, client = await prepare_admin(create_admin)
    token = await client.token('admin', 'admin')
    assert token

    with pytest.raises(client.JsonRestError) as ctx:
        await client.token('admin', 'badpassword')
    msg = {'error': 'Wrong username or password'}
    assert ctx.value.status_code == 401
    assert ctx.value.error_json == msg


@pytest.mark.parametrize('admin_type', ADMIN_TYPE_LIST)
@pytest.mark.run_loop
async def test_token_invalid_payload(create_admin):
    _, client = await prepare_admin(create_admin)
    data = {"foo": "bar"}
    with pytest.raises(client.JsonRestError) as ctx:
        resp = await client.request('POST', 'admin/token', data=data)
        await client.handle_response(resp)
    msg = {'error': 'Invalid json payload',
           'error_details': {'foo': 'foo is not allowed key',
                             'password': 'is required',
                             'username': 'is required'}}
    assert ctx.value.status_code == 400
    assert ctx.value.error_json == msg


@pytest.mark.parametrize('admin_type', ADMIN_TYPE_LIST)
@pytest.mark.run_loop
async def test_logout(create_admin):
    _, client = await prepare_admin(create_admin)
    token = await client.token('admin', 'admin')
    await client.destroy_token(token)

    with pytest.raises(client.JsonRestError) as ctx:
        resp = await client.request('DELETE', 'admin/logout')
        await client.handle_response(resp)

    msg = {'error': 'Auth header is not present, can not destroy token'}
    assert ctx.value.status_code == 400
    assert ctx.value.error_json == msg
