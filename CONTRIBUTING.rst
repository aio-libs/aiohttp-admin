Contributing
============

Running Tests
-------------

.. _GitHub: https://github.com/aio-libs/aiohttp_admin

Thanks for your interest in contributing to ``aiohttp_admin``, there are multiple
ways and places you can contribute.

Fist of all just clone repository::

    $ git clone git@github.com:aio-libs/aiohttp_admin.git

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


Reporting an Issue
------------------
If you have found issue with `aiohttp-admin` please do
not hesitate to file an issue on the GitHub_ project. When filing your
issue please make sure you can express the issue with a reproducible test
case.

When reporting an issue we also need as much information about your environment
that you can include. We never know what information will be pertinent when
trying narrow down the issue. Please include at least the following
information:

* Version of `aiohttp-admin` and `python`.
* Version of database.
* Platform you're running on (OS X, Linux, Windows).


.. _docker: https://www.docker.com/
.. _instruction: https://docs.docker.com/engine/installation/linux/ubuntulinux/
.. _docker-machine: https://docs.docker.com/machine/
