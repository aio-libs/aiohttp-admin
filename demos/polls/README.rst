Polls (demo for aiohttp)
========================

Example of polls project using aiohttp_, aiopg_ and aiohttp_jinja2_,
similar to django one.

Installation
============

Clone repo and install library::

    $ git clone git@github.com:aio-libs/aiohttp_admin.git
    $ cd aiohttp_admin
    $ pip install -e .
    $ pip install -r requirements-dev.txt

Install the app::

    $ cd demos/polls
    $ pip install -e .

Create database for your project with fake data::

    make docker_start_pg
    make fake_data

Run application::

    $ python -m aiohttpdemo_polls


Open browser::

    http://127.0.0.1:9002/admin


Requirements
============
* aiohttp_
* aiopg_
* aiohttp_jinja2_


.. _Python: https://www.python.org
.. _aiohttp: https://github.com/KeepSafe/aiohttp
.. _aiopg: https://github.com/aio-libs/aiopg
.. _aiohttp_jinja2: https://github.com/aio-libs/aiohttp_jinja2
