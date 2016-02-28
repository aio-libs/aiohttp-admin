import pytest
import aiohttp_admin
from aiohttp_admin.backends.mongo import MotorResource


@pytest.fixture
def create_admin(loop, create_app_and_client, mongo_collection,
                 document_schema):
    async def f(resource_name='test_post'):
        app, client = await create_app_and_client()
        admin = aiohttp_admin.setup(app, './')
        admin.add_resource(MotorResource(mongo_collection, document_schema,
                                         url=resource_name))
        return admin, client
    return f


@pytest.mark.run_loop
async def test_basic_rest(create_document, loop, create_admin):
    admin, client = await create_admin()
    document_num = 10
    await create_document(document_num)
    resp = await client.list('test_post')
    assert len(resp) == document_num

    entity_id = resp[0]['_id']
    entity = await client.detail('test_post', entity_id)
    assert entity == resp[0]
