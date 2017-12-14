aiohttp_admin
=============
.. image:: https://travis-ci.org/aio-libs/aiohttp_admin.svg?branch=master
    :target: https://travis-ci.org/aio-libs/aiohttp_admin
.. image:: https://codecov.io/gh/aio-libs/aiohttp_admin/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/aio-libs/aiohttp_admin

**aiohttp_admin** will help you on building an admin interface
on top of an existing data model. Library designed to be database agnostic and
decoupled of any ORM or database layer. Admin module relies on async/await syntax (PEP492)
thus *not* compatible with Python older than 3.5.


.. image:: https://raw.githubusercontent.com/aio-libs/aiohttp_admin/master/docs/demo.gif
    :align: center

Design
------
**aiohttp_admin** using following design philosophy:

- backend and frontend of admin views are decoupled by REST API as a
  result it is possible to change admin views without changing any **python**
  code. On browser side user interacts with single page application (ng-admin).

- admin views are database agnostic, if it is possible to implement REST API
  it should be straightforward to add admin views. Some filtering features may
  be disabled if database do not support some kind of filtering.


.. image:: https://cdn.rawgit.com/aio-libs/aiohttp_admin/master/docs/diagram2.svg
    :align: center
    :scale: 60 %


.. include:: CONTRIBUTING.rst


Supported backends
------------------

* PostgreSQL with, aiopg_ and sqlalchemy.core_
* MySQL with aiomysql_ and sqlalchemy.core_
* Mongodb with motor_


Mailing List
------------

https://groups.google.com/forum/#!forum/aio-libs


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
