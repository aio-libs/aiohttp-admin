import os
import time
from pathlib import Path

import psycopg2
import pymongo
import pymysql
import pytest

from docker import APIClient
from docker import from_env

TEMP_FOLDER = Path('/tmp') / 'aiohttp_admin'


def pytest_addoption(parser):
    parser.addoption("--no-pull", action="store_true", default=False,
                     help=("Do not pull docker images"))


@pytest.fixture(scope='session')
def docker_pull(request):
    return not request.config.getoption("--no-pull")


@pytest.fixture(scope='session')
def session_id():
    """Unique session identifier, random string."""
    return 'aiohttp-admin-session'


@pytest.fixture(scope='session')
def host():
    return os.environ.get('DOCKER_MACHINE_IP', '127.0.0.1')


@pytest.fixture(scope='session')
def docker():
    if os.environ.get('DOCKER_MACHINE_IP') is not None:
        docker = from_env(assert_hostname=False)
    else:
        docker = APIClient(version='auto')
    return docker


@pytest.fixture(scope='session')
def pg_params(pg_server):
    return dict(**pg_server['params'])


@pytest.fixture(scope='session')
def container_starter(request, docker, session_id, docker_pull):

    def f(image, internal_port, host_port, env=None, volume=None,
          command=None):
        if docker_pull:
            print("Pulling {} image".format(image))
            docker.pull(image)

        if volume is not None:
            host_vol, cont_vol = volume
            host_config = docker.create_host_config(
                port_bindings={internal_port: host_port},
                binds={host_vol: cont_vol})
            volumes = [cont_vol]
        else:
            host_config = docker.create_host_config(
                port_bindings={internal_port: host_port})
            volumes = None

        container = docker.create_container(
            image=image,
            name='{}-server-{}'.format(image.replace(":", "-"), session_id),
            ports=[internal_port],
            detach=True,
            environment=env,
            volumes=volumes,
            command=command,
            host_config=host_config)
        docker.start(container=container['Id'])

        def fin():
            docker.kill(container=container['Id'])
            docker.remove_container(container['Id'], v=True)

        request.addfinalizer(fin)
        container['port'] = host_port
        return container

    return f


def wait_for_container(callable, image, skip_exception):
    delay = 0.001
    for i in range(100):
        try:
            callable()
            break
        except skip_exception as e:
            print("Waiting image to start, last exception: {}".format(e))
            time.sleep(delay)
            delay *= 2
    else:
        pytest.fail("Cannot start {} server".format(image))


@pytest.fixture(scope='session')
def pg_server(host, unused_port, container_starter):
    tag = "9.6"
    image = 'postgres:{}'.format(tag)

    internal_port = 5432
    host_port = unused_port()
    environment = {'POSTGRES_USER': 'aiohttp_admin_user',
                   'POSTGRES_PASSWORD': 'mysecretpassword',
                   'POSTGRES_DB': 'aiohttp_admin'}

    volume = (str(TEMP_FOLDER / 'docker' / 'pg'),
              '/var/lib/postgresql/data')
    container = container_starter(image, internal_port, host_port,
                                  environment, volume)

    params = dict(database='aiohttp_admin',
                  user='aiohttp_admin_user',
                  password='mysecretpassword',
                  host=host,
                  port=host_port)

    def connect():
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.close()
        conn.close()

    wait_for_container(connect, image, psycopg2.Error)
    container['params'] = params
    return container


@pytest.fixture
def mysql_params(mysql_server):
    return dict(**mysql_server['params'])


@pytest.fixture(scope='session')
def mysql_server(host, unused_port, container_starter):
    tag = '5.7'
    image = 'mysql:{}'.format(tag)

    internal_port = 3306
    host_port = unused_port()
    environment = {'MYSQL_USER': 'aiohttp_admin_user',
                   'MYSQL_PASSWORD': 'mysecretpassword',
                   'MYSQL_DATABASE': 'aiohttp_admin',
                   'MYSQL_ROOT_PASSWORD': 'mysecretpassword'}
    volume = str(TEMP_FOLDER / 'docker' / 'mysql'), '/var/lib/mysql'
    container = container_starter(image, internal_port, host_port,
                                  environment, volume)

    params = dict(database='aiohttp_admin',
                  user='aiohttp_admin_user',
                  password='mysecretpassword',
                  host=host,
                  port=host_port)

    def connect():
        conn = pymysql.connect(**params)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()

    wait_for_container(connect, image, pymysql.Error)
    container['params'] = params
    return container


@pytest.fixture
def mongo_params(mongo_server):
    return dict(**mongo_server['params'])


@pytest.fixture(scope='session')
def mongo_server(host, unused_port, container_starter):
    tag = '3.3'
    image = 'mongo:{}'.format(tag)

    internal_port = 27017
    host_port = unused_port()
    volume = str(TEMP_FOLDER / 'docker' / 'mongo'), '/data/db'
    command = '--smallfiles'
    container = container_starter(image, internal_port, host_port,
                                  volume=volume, command=command)

    params = dict(host=host, port=host_port)

    def connect():
        client = pymongo.MongoClient(**params)
        test_coll = client.test.test
        test_coll.find_one()
        client.close()

    wait_for_container(connect, image, pymongo.errors.PyMongoError)
    container['params'] = params
    return container
