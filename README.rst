aiohttp_admin
=============
.. image:: https://travis-ci.org/jettify/aiohttp_admin.svg?branch=master
    :target: https://travis-ci.org/jettify/aiohttp_admin
.. image:: https://coveralls.io/repos/github/jettify/aiohttp_admin/badge.svg?branch=master
    :target: https://coveralls.io/github/jettify/aiohttp_admin?branch=master

**aiohttp_admin** will help you on building an admin interface
on top of an existing data model.

**aiohttp_admin** using following design philosophy:

1) backend and frontend of admin views are decoupled by REST API as
result it is possible to change admin views without changing any **python**
code. On browser side user interacts with single page application (ng-admin).

.. image:: https://raw.githubusercontent.com/jettify/aiohttp_admin/master/docs/diagram.svg
    :align: center

2) admin views are database agnostic, if it is possible to implement REST API
it should be strait forward to add admin views. Some filtering features may
be disabled if database do not support some kind of filtering.




.. image:: https://raw.githubusercontent.com/jettify/aiohttp_admin/master/docs/admin_polls.png
    :align: center

Run Tests
---------
Fist of all just clone repository::

    $ git clone git@github.com:jettify/aiohttp_admin.git

Install docker_ using instruction_ from the official site, for OSX we
use docker-machine_.

Create virtualenv with python3.5 (older version are not supported). For example
using *virtualenvwrapper* commands could look like::

   $ cd aiohttp_admin
   $ mkvirtualenv --python=`which python3.5` aiohttp_admin


After that please install libraries required for development::

   $ pip install -r requirements-dev.txt

Congratulations, you are ready to run the test suite::

    $ py.test --dp -s -v ./tests

Under the hood python docker client pulls images for PostgreSQL, MySQL
and Mongodb. Fixtures start databases and insert testing data. You do not
have to install any database at all.

Next time  `--dp` (docker pull) flag could be dropped since all required
images are cached on local machine. To make sure you have required images
please execute::

    $ docker images

Among results you should find something like::

    postgres  9.5  247a11721cbd  2 weeks ago  265.9 MB
    mysql     5.7  63a92d0c131d  8 weeks ago  374.1 MB
    mongo     2.6  150dd5b5bd1b  9 weeks ago  390.9 MB


For OSX users one extra step is required, before running tests, please
init environment variables::

    $ eval $(docker-machine env default)
    $ export DOCKER_MACHINE_IP=$(docker-machine ip)


Supported backends
------------------

* PostgreSQL with, aiopg_ and sqlalchemy.core_
* MySQL with aiomysql_ and sqlalchemy.core_
* Mongodb with motor_



Requirements
------------

* Python_ 3.5+
* aiopg_ or aiomysql_ or motor_


.. _Python: https://www.python.org
.. _asyncio: http://docs.python.org/3.4/library/asyncio.html
.. _aiopg: https://github.com/aio-libs/aiopg
.. _aiomysql: https://github.com/aio-libs/aiomysql
.. _motor: https://github.com/mongodb/motor
.. _sqlalchemy.core: http://www.sqlalchemy.org/
.. _PEP492: https://www.python.org/dev/peps/pep-0492/
.. _docker: https://www.docker.com/
.. _instruction: https://docs.docker.com/engine/installation/linux/ubuntulinux/
.. _docker-machine: https://docs.docker.com/machine/
