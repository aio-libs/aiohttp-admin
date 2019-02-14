import pytest
from functools import partial
import aiohttp_security

from aiohttp_admin.security import DummyAuthPolicy, DummyTokenIdentityPolicy
from aiohttp_admin.security import Permissions

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
async def test_list_without_permisson(create_admin):
    p = [Permissions.edit, Permissions.add, Permissions.delete]
    resource, client = await prepare_admin(create_admin, p)
    token = await client.token('admin', 'admin')

    with pytest.raises(client.JsonRestError) as ctx:
        await client.list(resource, token=token)

    assert ctx.value.status_code == 401
    msg = {'error': 'User has no permission aiohttp_admin.view'}
    assert ctx.value.error_json == msg
