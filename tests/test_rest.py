import pytest


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_basic_rest(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)

    # TODO this is ugly
    primary_key = admin._resources[0]._primary_key

    num_entities = 10
    await create_entities(num_entities)
    resp = await client.list(resource)
    assert len(resp) == num_entities

    entity_id = resp[0][primary_key]
    entity = await client.detail(resource, entity_id)
    assert entity == resp[0]


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_detail_entity_that_not_exists(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)

    primary_key = admin._resources[0]._primary_key

    # create one entity
    num_entities = 1
    await create_entities(num_entities)

    # make sure we have only one
    resp = await client.list(resource)
    assert len(resp) == 1

    # delete create entity
    entity_id = resp[0][primary_key]
    await client.delete(resource, entity_id)

    # make sure our table/collection is empty
    resp = await client.list(resource, page=1, per_page=30)
    assert len(resp) == 0

    with pytest.raises(Exception) as ctx:
        await client.detail(resource, entity_id)

    err = ctx.value
    assert err.status_code == 404
    err_dict = {'error': 'Entity with id: %s not found' % entity_id}
    assert err.error_json == err_dict


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_list_pagination(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)
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


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_list_filtering_by_pk(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)
    # TODO this is ugly
    primary_key = admin._resources[0]._primary_key

    num_entities = 25
    await create_entities(num_entities)
    all_rows = await client.list(resource, page=1, per_page=30)
    assert len(all_rows) == num_entities

    entity = all_rows[0]
    entity_id = entity[primary_key]

    # filter by primary key
    filters = {primary_key: entity_id}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 1
    assert entity == resp[0]


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_list_text_like_filtering(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)
    # TODO this is ugly

    num_entities = 25
    await create_entities(num_entities)
    all_rows = await client.list(resource, page=1, per_page=30)
    assert len(all_rows) == num_entities

    filters = {'category': {'like': 'category'}}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 25

    filters = {'category': {'like': 'category field 2'}}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 6


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_list_q_filter(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)
    # TODO this is ugly

    num_entities = 25
    await create_entities(num_entities)
    all_rows = await client.list(resource, page=1, per_page=30)
    assert len(all_rows) == num_entities

    # text  search on sa.String field
    filters = {'q': 'category field 2'}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 6

    # text  search on sa.Text field
    filters = {'q': 'body field 2'}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 6


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_list_sorting(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)
    num_entities = 25
    await create_entities(num_entities)

    rows = await client.list(resource, page=1, per_page=30, sort_field='views',
                             sort_dir='ASC')

    assert len(rows) == num_entities
    sorted_values = [r['views'] for r in rows]
    expected = list(range(0, num_entities))
    assert sorted_values == expected

    rows = await client.list(resource, page=1, per_page=30, sort_field='views',
                             sort_dir='DESC')

    assert len(rows) == num_entities
    sorted_values = [r['views'] for r in rows]
    assert sorted_values == expected[::-1]


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_list_filtering(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)

    num_entities = 25
    await create_entities(num_entities)
    all_rows = await client.list(resource, page=1, per_page=30)
    assert len(all_rows) == num_entities

    filters = {'views': 5}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 1
    assert resp[0]['views'] == 5

    filters = {'views': {'gt': 15}}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 9

    filters = {'views': {'ge': 15}}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 10

    filters = {'views': {'eq': 15}}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 1

    filters = {'views': {'ne': 15}}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 24

    filters = {'views': {'le': 15}}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 16

    filters = {'views': {'lt': 15}}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 15

    filters = {'views': {'in': [1, 2, 3]}}
    resp = await client.list(resource, page=1, per_page=30, filters=filters)
    assert len(resp) == 3


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_create(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)
    # TODO this is ugly
    primary_key = admin._resources[0]._primary_key

    num_entities = 1
    await create_entities(num_entities)

    entity = {'title': 'title test_create',
              'category': 'category field',
              'body': 'body field',
              'views': 42,
              'average_note': 0.1,
              # 'pictures': {'foo': 'bar', 'i': 5},
              'published_at': '2016-02-27T22:33:04',
              # 'tags': [1, 2, 3],
              'status': 'c',
              'visible': True}

    resp = await client.create(resource, entity)
    row_list = await client.list(resource)
    assert len(row_list) == num_entities + 1
    assert primary_key in resp
    assert resp['title'] == entity['title']


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_update(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)
    # TODO this is ugly
    primary_key = admin._resources[0]._primary_key

    num_entities = 1
    await create_entities(num_entities)

    entity = {'title': 'updated title',
              'category': 'category field',
              'body': 'body field',
              'views': 88,
              'average_note': 0.7,
              # 'pictures': {'x': 1},
              'published_at': '2016-02-27T22:33:04',
              # 'tags': [1, 2, 3],
              'status': 'c',
              'visible': True}

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


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_update_deleted_entity(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)
    primary_key = admin._resources[0]._primary_key

    num_entities = 1
    await create_entities(num_entities)

    resp = await client.list(resource)
    assert len(resp) == 1
    entity_id = resp[0][primary_key]
    await client.delete(resource, entity_id)

    entity = {'title': 'updated title',
              'category': 'category field',
              'body': 'body field',
              'views': 88,
              'average_note': 0.7,
              # 'pictures': {'x': 1},
              'published_at': '2016-02-27T22:33:04',
              # 'tags': [1, 2, 3],
              'status': 'c',
              'visible': True}

    with pytest.raises(Exception) as ctx:
        await client.update(resource, entity_id, entity)

    err = ctx.value
    assert err.status_code == 404
    err_dict = {'error': 'Entity with id: %s not found' % entity_id}
    assert err.error_json == err_dict


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_update_not_valid_payload(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)
    primary_key = admin._resources[0]._primary_key

    num_entities = 1
    await create_entities(num_entities)

    resp = await client.list(resource)
    assert len(resp) == 1
    entity_id = resp[0][primary_key]

    # try to send not json
    with pytest.raises(Exception) as ctx:
        await client.update(resource, entity_id, 'foo', json_dumps=False)

    err = ctx.value
    err_dict = {'error': 'Payload is not json serialisable'}
    assert err.status_code == 400
    assert err.error_json == err_dict

    # try to send invalid payload
    with pytest.raises(Exception) as ctx:
        await client.update(resource, entity_id, {'foo': 'bar'})

    err = ctx.value
    assert err.status_code == 400
    assert err.error_json['error'] == 'Json in payload invalid'
    foo_error = err.error_json['error_details']['foo']
    assert foo_error == 'foo is not allowed key'


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_delete(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)
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


@pytest.mark.parametrize('admin_type', pytest.admin_type_list)
@pytest.mark.run_loop
async def test_delete_entity_that_not_exists(create_admin):
    resource = 'posts'
    admin, client, create_entities = await create_admin(resource)
    token = await client.token('admin', 'admin')
    client.set_token(token)
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
