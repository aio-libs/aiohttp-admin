import pytest
import trafaret as t
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from aiohttp_admin.backends.sa_utils import validator_from_table


@pytest.fixture
def table():

    meta = sa.MetaData()
    post = sa.Table(
        'post', meta,
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('views', sa.Integer, nullable=False),
        sa.Column('average_note', sa.Float, nullable=False),
        sa.Column('pictures', postgresql.JSON, server_default='{}'),
        sa.Column('published_at', sa.Date, nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.Integer), server_default='[]'),

        # Indexes #
        sa.PrimaryKeyConstraint('id', name='post_id_pkey'))
    return post


def test_keys(table):
    names = sorted(['id', 'title', 'body', 'views', 'average_note', 'pictures',
                    'published_at', 'tags'])
    traf = validator_from_table(table, skip_pk=False)
    result_names = sorted([key.name for key in traf.keys])
    assert result_names == names


def test_skip_pk(table):
    names = sorted(['title', 'body', 'views', 'average_note', 'pictures',
                    'published_at', 'tags'])
    traf = validator_from_table(table, skip_pk=True)
    result_names = sorted([key.name for key in traf.keys])
    assert result_names == names


def test_validation(table):
    traf = validator_from_table(table, skip_pk=False)
    data = {'id': '1',
            'title': 'title string',
            'body': 'body text',
            'views': '42',
            'average_note': '0.11',
            'pictures': {'foo': 'bar'},
            'published_at': '2015-12-15',
            'tags': [1, 2, 3]}
    data = traf(data)
    assert data['id'] == 1
    assert data['views'] == 42
    assert data['average_note'] == 0.11


def test_validation_bad_input(table):
    traf = validator_from_table(table, skip_pk=False)
    with pytest.raises(t.DataError):
        data = {'id': 'not a string',
                'title': 'title string',
                'body': 'body text',
                'views': 42,
                'average_note': 0.11,
                'pictures': {'foo': 'bar'},
                'published_at': '2015-12-15',
                'tags': [1, 2, 3]}
        traf(data)

    with pytest.raises(t.DataError):
        data = {}
        traf(data)
