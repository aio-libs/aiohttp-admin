import json

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from aiohttp_admin.contrib.admin import Schema
from aiohttp_admin.contrib import models
from aiohttp_admin.backends.sa import PGResource, MySQLResource


def test_create_model():
    class Test(models.ModelAdmin):
        fields = ('id', )

    test = Test()

    assert test.to_dict()['name'] == 'test'


def test_create_schema():
    CUSTOM_ADMIN_NAME = 'My admin'

    schema = Schema(title=CUSTOM_ADMIN_NAME)
    data = json.loads(schema.to_json())

    assert data['title'] == CUSTOM_ADMIN_NAME
    assert len(data['endpoints']) == 0


def test_registration_model(initialize_base_schema):
    schema = initialize_base_schema
    data = json.loads(schema.to_json())

    assert data['title'] == 'Admin'
    assert len(data['endpoints']) == 2


# TODO: added Mongo
@pytest.mark.parametrize('resources', [
    PGResource,
    MySQLResource,
])
def test_get_type_of_fields(resources):
    table = sa.Table(
        'Test', sa.MetaData(),
        sa.Column('integer', sa.Integer, primary_key=True),
        sa.Column('text', sa.Text),
        sa.Column('float', sa.Float),
        sa.Column('date', sa.Date),
        sa.Column('boolean', sa.Boolean),
        sa.Column('json', postgresql.JSON),
    )
    fields = ['integer', 'text', 'float', 'date', 'boolean', 'json', ]

    data_type_fields = resources.get_type_of_fields(fields, table)
    expected_type_fields = {
        'integer': 'integer',
        'text': 'string',
        'float': 'number',
        'date': 'date',
        'boolean': 'bool',
        'json': 'json',
    }

    assert data_type_fields == expected_type_fields

    fields = None
    data_type_fields = resources.get_type_of_fields(fields, table)
    expected_type_fields = {
        'integer': 'integer',
    }

    assert data_type_fields == expected_type_fields
