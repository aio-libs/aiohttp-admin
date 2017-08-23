import json
import pytest
import trafaret as t

from bson import ObjectId

from aiohttp_admin.exceptions import JsonValidaitonError
from aiohttp_admin.utils import (validate_query_structure, jsonify,
                                 validate_payload, as_dict, SimpleType)


def test_validate_query_empty_defaults():
    q = validate_query_structure({})
    expected = {'_page': 1,
                '_perPage': 30,
                '_sortDir': 'DESC'}
    assert q == expected


def test_validate_query_all_possible_params():
    filters = {'views': {'ge': 20},
               'id': {'in': [1, 2, 3]}}

    query = {'_page': 1,
             '_perPage': 30,
             '_sortField': 'id',
             '_sortDir': 'DESC',
             '_filters': json.dumps(filters)}
    q = validate_query_structure(query)

    expected = query.copy()
    expected['_filters'] = filters
    assert q == expected
    
    
def test_simple_type():
    assert 42 == SimpleType(42)
    assert 13.37 == SimpleType(13.37)
    assert True is SimpleType(True)
    assert 'string' == SimpleType('string')
    assert '42' == SimpleType('42')
    assert '13.37' == SimpleType('13.37')


def test_validate_query_numeric_string():
    filters = {
        'views': "20"
    }

    query = {'_page': 1,
             '_perPage': 30,
             '_sortField': 'id',
             '_sortDir': 'DESC',
             '_filters': json.dumps(filters)}
    q = validate_query_structure(query)

    expected = query.copy()
    expected['_filters'] = filters
    assert q == expected


def test_validate_query_filters_is_not_json():
    query = {'_filters': 'foo'}

    with pytest.raises(JsonValidaitonError) as ctx:
        validate_query_structure(query)
    error = json.loads(ctx.value.text)
    assert error['error'] == '_filters field can not be serialized'


def test_validate_query_filters_invalid():
    query = {'_filters': json.dumps({'foo': {'bar': 'baz'}})}

    with pytest.raises(JsonValidaitonError) as ctx:
        validate_query_structure(query)

    error = json.loads(ctx.value.text)
    assert error['error'] == '_filters query invalid'


def test_jsonify():
    obj = {'foo': 'bar'}
    jsoned = jsonify(obj)
    assert jsoned == '{"foo": "bar"}'


def test_jsonify_object_id():
    obj = {'foo': ObjectId('1' * 24)}
    jsoned = jsonify(obj)
    assert jsoned == '{"foo": "111111111111111111111111"}'


def test_jsonify_failed():
    with pytest.raises(TypeError):
        jsonify(object())


def test_validate_payload():
    raw_data = b'{"foo": "bar"}'
    schema = t.Dict({
        t.Key('foo'): t.Atom('bar')
    })
    data = validate_payload(raw_data, schema)
    assert data == {'foo': 'bar'}


def test_validate_payload_not_json():
    raw_data = b'foo=bar'
    schema = t.Dict({
        t.Key('foo'): t.Atom('bar')
    })

    with pytest.raises(JsonValidaitonError) as ctx:
        validate_payload(raw_data, schema)

    error = json.loads(ctx.value.text)
    assert error['error'] == 'Payload is not json serialisable'


def test_validate_payload_not_valid_schema():
    raw_data = b'{"baz": "bar"}'
    schema = t.Dict({
        t.Key('foo'): t.Atom('bar')
    })

    with pytest.raises(JsonValidaitonError) as ctx:
        validate_payload(raw_data, schema)

    error = json.loads(ctx.value.text)
    assert error['error'] == 'Invalid json payload'


def test_as_dict():
    exc = t.DataError()
    resp = as_dict(exc)
    assert isinstance(resp, dict)

    exc = t.DataError()
    assert isinstance(exc.as_dict("boom"), str)

    resp = as_dict(exc, 'boom')
    assert isinstance(resp, dict)
