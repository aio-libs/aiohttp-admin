aiohttp-admin
=============
.. image:: https://codecov.io/gh/aio-libs/aiohttp-admin/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/aio-libs/aiohttp-admin

**aiohttp-admin** allows you to create a admin interface in minutes. It is designed to
be flexible and database agnostic.

It has built-in support for SQLAlchemy, allowing admin views to be created automatically
from DB models (ORM or core).

To see how to use the 0.1 versions, please refer to the examples. Documentation will be updated at a later date.

Development
-----------

To develop or build the project from source, you'll need to build the admin JS file::

    cd admin-js/
    yarn install
    yarn build

After that, it can be treated as any other Python project.
