import os
import time

import psycopg2
import pymongo
import pymysql
import pytest

from docker import Client as DockerClient


def pytest_addoption(parser):
    parser.addoption("--dp", action="store_true", default=False,
                     help=("Force docker pull"))


@pytest.fixture(scope='session')
def docker_pull(request):
    return request.config.getoption("--dp")


@pytest.fixture(scope='session')
def session_id():
    """Unique session identifier, random string."""
    return 'aiohttp-admin-session'


@pytest.fixture(scope='session')
def docker():
    if os.environ.get('DOCKER_MACHINE_IP') is not None:
        docker = DockerClient.from_env(assert_hostname=False)
    else:
        docker = DockerClient(version='auto')
    return docker


@pytest.fixture(scope='session')
def pg_params(pg_server):
    return dict(**pg_server['params'])


@pytest.fixture(scope='session')
def container_starter(request, docker, session_id, docker_pull):

    def f(image, internal_port, host_port, env=None):
        if docker_pull:
            print("Pulling {} image".format(image))
            docker.pull(image)

        container = docker.create_container(
            image=image,
            name='{}-server-{}'.format(image.replace(":", "-"), session_id),
            ports=[internal_port],
            detach=True,
            environment=env,
            host_config=docker.create_host_config(
                port_bindings={internal_port: host_port})
        )
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
        except skip_exception:
            time.sleep(delay)
            delay *= 2
    else:
        pytest.fail("Cannot start {} server".format(image))


@pytest.fixture(scope='session')
def pg_server(unused_port, container_starter):
    tag = "9.5"
    image = 'postgres:{}'.format(tag)

    internal_port = 5432
    host_port = unused_port()

    container = container_starter(image, internal_port, host_port)

    host = os.environ.get('DOCKER_MACHINE_IP', '127.0.0.1')
    params = dict(database='postgres',
                  user='postgres',
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
def mysql_server(unused_port, container_starter):
    tag = '5.7'
    image = 'mysql:{}'.format(tag)

    internal_port = 3306
    host_port = unused_port()
    environment = {'MYSQL_USER': 'aiohttp_admin',
                   'MYSQL_PASSWORD': 'mysecretpassword',
                   'MYSQL_DATABASE': 'aiohttp_admin',
                   'MYSQL_ROOT_PASSWORD': 'mysecretpassword'}

    container = container_starter(image, internal_port, host_port, environment)

    host = os.environ.get('DOCKER_MACHINE_IP', '127.0.0.1')
    params = dict(database='aiohttp_admin',
                  user='aiohttp_admin',
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
def mongo_server(unused_port, container_starter):
    tag = '2.6'
    image = 'mongo:{}'.format(tag)

    internal_port = 27017
    host_port = unused_port()
    container = container_starter(image, internal_port, host_port)

    host = os.environ.get('DOCKER_MACHINE_IP', '127.0.0.1')
    params = dict(host=host, port=host_port)

    def connect():
        client = pymongo.MongoClient(**params)
        test_coll = client.test.test
        test_coll.find_one()
        client.close()

    wait_for_container(connect, image, pymongo.errors.PyMongoError)
    container['params'] = params
    return container
