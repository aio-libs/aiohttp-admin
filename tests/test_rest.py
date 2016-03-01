import pytest
import aiohttp_admin
from aiohttp_admin.backends.sa import SAResource
from aiohttp_admin.backends.mongo import MotorResource


@pytest.fixture
def admin_type():
    return 'sa'


@pytest.fixture
def create_admin(loop, admin_type, create_app_and_client,
                 mongo_collection, document_schema, create_document,
                 postgres, sa_table, create_table):

    async def sa(resource_name='test_post'):
        app, client = await create_app_and_client()
        admin = aiohttp_admin.setup(app, './')
        admin.add_resource(SAResource(postgres, sa_table, url=resource_name))
        return admin, client, create_table

    async def mongo(resource_name='test_post'):
        app, client = await create_app_and_client()
        admin = aiohttp_admin.setup(app, './')
        admin.add_resource(MotorResource(mongo_collection, document_schema,
                                         url=resource_name))
        return admin, client, create_document
    if admin_type == 'mongo':
        f = mongo
    else:
        f = sa
    return f


@pytest.mark.parametrize('admin_type', ['sa', 'mongo'])
@pytest.mark.run_loop
async def test_basic_rest(create_admin, loop):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    # TODO this is ugly
    primary_key = admin._resources[0]._primary_key

    num_entities = 10
    await create_entities(num_entities)
    resp = await client.list(resource)
    assert len(resp) == num_entities

    entity_id = resp[0][primary_key]
    entity = await client.detail(resource, entity_id)
    assert entity == resp[0]


@pytest.mark.parametrize('admin_type', ['sa', 'mongo'])
@pytest.mark.run_loop
async def test_list_pagination(create_admin, loop):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    # TODO this is ugly
    primary_key = admin._resources[0]._primary_key

    num_entities = 25
    await create_entities(num_entities)

    all_rows = await client.list(resource, page=1, per_page=30)
    assert len(all_rows) == num_entities
    all_ids = {r[primary_key] for r in all_rows}

    page1 = await client.list(resource, page=1, per_page=15)
    page2 = await client.list(resource, page=2, per_page=15)
    assert len(page1) == 15
    assert len(page2) == 10

    paged_ids = {r[primary_key] for r in page1 + page2}
    assert set(all_ids) == set(paged_ids)


@pytest.mark.parametrize('admin_type', ['sa', 'mongo'])
@pytest.mark.run_loop
async def test_create(create_admin, loop):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    # TODO this is ugly
    primary_key = admin._resources[0]._primary_key

    num_entities = 1
    await create_entities(num_entities)

    entity = {'title': 'title test_create',
              'category': 'category field',
              'body': 'body field',
              'views': 42,
              'average_note': 0.1,
              'pictures': {'foo': 'bar', 'i': 5},
              'published_at': '2016-02-27T22:33:04.549000',
              'tags': [1, 2, 3],
              'status': 'c'}
    resp = await client.create(resource, entity)
    row_list = await client.list(resource)
    assert len(row_list) == num_entities + 1
    assert primary_key in resp
    assert resp['title'] == entity['title']


@pytest.mark.parametrize('admin_type', ['sa', 'mongo'])
@pytest.mark.run_loop
async def test_update(create_admin, loop):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    # TODO this is ugly
    primary_key = admin._resources[0]._primary_key

    num_entities = 1
    await create_entities(num_entities)

    entity = {'title': 'updated title',
              'category': 'category field',
              'body': 'body field',
              'views': 88,
              'average_note': 0.7,
              'pictures': {'x': 1},
              'published_at': '2016-02-27T22:33:04.549000',
              'tags': [1, 2, 3],
              'status': 'c'}

    resp = await client.list(resource)
    assert len(resp) == 1
    entity_id = resp[0][primary_key]

    new_entity = await client.update(resource, entity_id, entity)
    entity[primary_key] = entity_id
    assert new_entity == entity

    resp = await client.list(resource)
    assert len(resp) == 1
    new_entity = resp[0]
    assert new_entity == entity


@pytest.mark.parametrize('admin_type', ['sa', 'mongo'])
@pytest.mark.run_loop
async def test_delete(create_admin, loop):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    # TODO this is ugly
    primary_key = admin._resources[0]._primary_key

    num_entities = 5
    await create_entities(num_entities)

    all_rows = await client.list(resource, page=1, per_page=30)
    assert len(all_rows) == num_entities
    all_ids = {r[primary_key] for r in all_rows}

    for entity_id in all_ids:
        await client.delete(resource, entity_id)

    all_rows = await client.list(resource, page=1, per_page=30)
    assert len(all_rows) == 0


@pytest.mark.parametrize('admin_type', ['sa', 'mongo'])
@pytest.mark.run_loop
async def test_delete_entity_that_not_exists(create_admin, loop):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    # TODO this is ugly
    primary_key = admin._resources[0]._primary_key

    num_entities = 1
    await create_entities(num_entities)

    resp = await client.list(resource, page=1, per_page=30)
    assert len(resp) == 1
    entity_id = resp[0][primary_key]

    # delete operation is idempotent
    await client.delete(resource, entity_id)
    all_rows = await client.list(resource, page=1, per_page=30)
    assert len(all_rows) == 0

    await client.delete(resource, entity_id)
    await client.delete(resource, entity_id)
