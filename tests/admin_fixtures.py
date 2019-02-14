import pytest
import sqlalchemy as sa
import aiohttp_admin
import aiohttp_security
from aiohttp_admin.backends.sa import PGResource, MySQLResource
from aiohttp_admin.backends.mongo import MotorResource
from aiohttp_admin.security import DummyAuthPolicy, DummyTokenIdentityPolicy
from aiohttp_admin.contrib.admin import Schema
from aiohttp_admin.contrib import models


def setup_security(app):
    # setup dummy auth and identity
    ident_policy = DummyTokenIdentityPolicy()
    auth_policy = DummyAuthPolicy(username="admin", password="admin")
    aiohttp_security.setup(app, ident_policy, auth_policy)


@pytest.fixture
def pg_admin_creator(loop, create_app_and_client, postgres,
                     sa_table, create_table):
    async def pg_admin(resource_name='test_post', security=setup_security):
        app, client, app_starter = await create_app_and_client()
        resources = (PGResource(postgres, sa_table, url=resource_name),)
        admin = aiohttp_admin.setup(app, '/', resources=resources)
        security(admin)
        app.add_subapp('/admin', admin)
        await app_starter()
        return admin, client, create_table
    return pg_admin


@pytest.fixture
def mysql_admin_creator(loop, create_app_and_client, mysql, sa_table,
                        create_table):
    async def mysql_admin(resource_name='test_post', security=setup_security):
        app, client, app_starter = await create_app_and_client()
        resources = (MySQLResource(mysql, sa_table, url=resource_name),)
        admin = aiohttp_admin.setup(app, '/', resources=resources)
        security(admin)
        app.add_subapp('/admin', admin)
        await app_starter()
        return admin, client, create_table
    return mysql_admin


@pytest.fixture
def mongo_admin_creator(loop, create_app_and_client, mongo_collection,
                        document_schema, create_document):
    async def mongo_admin(resource_name='test_post', security=setup_security):
        app, client, app_starter = await create_app_and_client()
        m = mongo_collection
        resources = (MotorResource(m, document_schema, url=resource_name),)
        admin = aiohttp_admin.setup(app, '/', resources=resources)
        security(admin)
        app.add_subapp('/admin', admin)
        await app_starter()
        return admin, client, create_document

    return mongo_admin


@pytest.fixture
def create_admin(request, admin_type):
    if admin_type == 'mongo':
        f = request.getfixturevalue('mongo_admin_creator')
    elif admin_type == 'mysql':
        f = request.getfixturevalue('mysql_admin_creator')
    else:
        f = request.getfixturevalue('pg_admin_creator')
    return f


@pytest.fixture
def initialize_base_schema():
    schema = Schema()

    @schema.register
    class Test(models.ModelAdmin):
        fields = ('id',)

        class Meta:
            resource_type = PGResource
            table = sa.Table(
                'test',
                sa.MetaData(),
                sa.Column('id', sa.Integer)
            )

    @schema.register
    class Test2(models.ModelAdmin):
        fields = ('id',)

        class Meta:
            resource_type = PGResource
            table = sa.Table(
                'test',
                sa.MetaData(),
                sa.Column('id', sa.Integer)
            )

    return schema
