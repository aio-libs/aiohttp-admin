aiohttp_admin
=============
.. image:: https://travis-ci.org/jettify/aiohttp_admin.svg?branch=master
    :target: https://travis-ci.org/jettify/aiohttp_admin
.. image:: https://coveralls.io/repos/github/jettify/aiohttp_admin/badge.svg?branch=master
    :target: https://coveralls.io/github/jettify/aiohttp_admin?branch=master

**aiohttp_admin** will help you on building an admin interface
on top of an existing data model.


Supported backends
------------------

* PostgreSQL with, aiopg_ and sqlalchemy.core_
* MySQL with aiomysql_ and sqlalchemy.core_
* Mongodb with motor


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
