Motortwit Demo
==============

Example of mongo project using aiohttp_, motor_ and aiohttp_jinja2_,
similar to flask one.

Installation
============

Install the app::

    $ cd demos/motorwtit
    $ pip install -e .

Create database for your project::

    make docker_start_mongo
    make fake_data


Run application::

    $ make run

Open browser::

    http://localhost:8080/


Requirements
============
* aiohttp_
* motor_
* aiohttp_jinja2_


.. _Python: https://www.python.org
.. _aiohttp: https://github.com/KeepSafe/aiohttp
.. _motor: https://github.com/mongodb/motor
.. _aiohttp_jinja2: https://github.com/aio-libs/aiohttp_jinja2
