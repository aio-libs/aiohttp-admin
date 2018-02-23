.. aiohttp-admin documentation master file, created by
   sphinx-quickstart on Sun Nov 13 21:04:19 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to aiohttp-admin!
=========================

.. image:: https://travis-ci.org/aio-libs/aiohttp_admin.svg?branch=master
    :target: https://travis-ci.org/aio-libs/aiohttp_admin
.. image:: https://codecov.io/gh/aio-libs/aiohttp_admin/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/aio-libs/aiohttp_admin


**aiohttp_admin** will help you on building an admin interface
on top of an existing data model. Library designed to be database agnostic and
decoupled of any ORM or datbase layer. Admin module relies on async/await syntax (PEP492)
thus *not* compatible with Python older than 3.5.


**What is aiohttp-admin use cases?**

- For small web applications or micro services, where custom admin interface is overkill.
- To give a manager something to play with while proper admin interface is not ready.
- Could be solution if you absolutely hate to write a lot of js/html but have to


.. image:: demo.gif
    :align: center

Features
--------

- designed to be used with aiohttp;
- library supports multiple database, out of the box MySQL, PostgreSQL, Mongodb;
- clear separation of backend and frontend layers;
- no WTForms, frontend is SPA;
- uvloop_ compatible, tests executed with both: default and uvloop
- database agnostic, if you can represent your entities with REST api, you can build admin views.


.. include:: contents.rst.inc


Ask Question
------------
Please feel free to ask question in `mail list <https://groups.google.com/forum/#!forum/aio-libs>`_
or raise issue on `github <https://github.com/aio-libs/aiohttp_admin/issues>`_

Requirements
------------

* Python_ 3.5+
* PostgreSQL with, aiopg_ and sqlalchemy.core_
* MySQL with aiomysql_ and sqlalchemy.core_
* Mongodb with motor_

.. _Python: https://www.python.org
.. _asyncio: http://docs.python.org/3.4/library/asyncio.html
.. _uvloop: https://github.com/MagicStack/uvloop
.. _aiopg: https://github.com/aio-libs/aiopg
.. _aiomysql: https://github.com/aio-libs/aiomysql
.. _motor: https://github.com/mongodb/motor
.. _sqlalchemy.core: http://www.sqlalchemy.org/
.. _PEP492: https://www.python.org/dev/peps/pep-0492/
.. _docker: https://www.docker.com/
.. _instruction: https://docs.docker.com/engine/installation/linux/ubuntulinux/
.. _docker-machine: https://docs.docker.com/machine/

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
