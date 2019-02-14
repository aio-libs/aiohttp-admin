import pytest
from functools import partial
import aiohttp_security

from aiohttp_admin.security import DummyAuthPolicy, DummyTokenIdentityPolicy

from db_fixtures import ADMIN_TYPE_LIST


def setup_security(app, permissions=None):
    # setup dummy auth and identity
    ident_policy = DummyTokenIdentityPolicy()
    auth_policy = DummyAuthPolicy(username="admin", password="admin",
                                  permissions=permissions)
    aiohttp_security.setup(app, ident_policy, auth_policy)


async def prepare_admin(create_admin, permissions=None):
    resource = 'posts'
    security = partial(setup_security, permissions=permissions)
    admin, client, create_entities = await create_admin(
        resource, security=security)
    num_entities = 10
    await create_entities(num_entities)
    return resource, client


@pytest.mark.parametrize('admin_type', ADMIN_TYPE_LIST)
@pytest.mark.run_loop
async def test_list_without_token(create_admin):
    resource, client = await prepare_admin(create_admin)

    with pytest.raises(client.JsonRestError) as ctx:
        await client.list(resource)
    assert ctx.value.status_code == 401

    with pytest.raises(client.JsonRestError) as ctx:
        bad_token = "bad_token"
        await client.list(resource, token=bad_token)
    assert ctx.value.status_code == 401


@pytest.mark.parametrize('admin_type', ADMIN_TYPE_LIST)
@pytest.mark.run_loop
async def test_details_without_token(create_admin):
    resource, client = await prepare_admin(create_admin)

    with pytest.raises(client.JsonRestError) as ctx:
        entity_id = 1
        await client.detail(resource, entity_id)
    assert ctx.value.status_code == 401

    with pytest.raises(client.JsonRestError) as ctx:
        bad_token = "bad_token"
        entity_id = 1
        await client.detail(resource, entity_id, token=bad_token)
    assert ctx.value.status_code == 401


@pytest.mark.parametrize('admin_type', ADMIN_TYPE_LIST)
@pytest.mark.run_loop
async def test_delete_without_token(create_admin):
    resource, client = await prepare_admin(create_admin)

    with pytest.raises(client.JsonRestError) as ctx:
        entity_id = 1
        await client.delete(resource, entity_id)
    assert ctx.value.status_code == 401

    with pytest.raises(client.JsonRestError) as ctx:
        bad_token = "bad_token"
        entity_id = 1
        await client.delete(resource, entity_id, token=bad_token)
    assert ctx.value.status_code == 401


@pytest.mark.parametrize('admin_type', ADMIN_TYPE_LIST)
@pytest.mark.run_loop
async def test_update_without_token(create_admin):
    resource, client = await prepare_admin(create_admin)
    entity = {}

    with pytest.raises(client.JsonRestError) as ctx:
        entity_id = 1
        await client.update(resource, entity_id, entity)
    assert ctx.value.status_code == 401

    with pytest.raises(client.JsonRestError) as ctx:
        bad_token = "bad_token"
        entity_id = 1
        await client.update(resource, entity_id, entity, token=bad_token)
    assert ctx.value.status_code == 401


@pytest.mark.parametrize('admin_type', ADMIN_TYPE_LIST)
@pytest.mark.run_loop
async def test_create_without_token(create_admin):
    resource, client = await prepare_admin(create_admin)
    entity = {}

    with pytest.raises(client.JsonRestError) as ctx:
        await client.create(resource, entity)
    assert ctx.value.status_code == 401

    with pytest.raises(client.JsonRestError) as ctx:
        bad_token = "bad_token"
        await client.create(resource, entity, token=bad_token)
    assert ctx.value.status_code == 401
