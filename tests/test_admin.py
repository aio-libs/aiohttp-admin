from aiohttp import web

import aiohttp_admin
from _auth import check_credentials


def test_path() -> None:
    app = web.Application()
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials},
                                    "resources": ()}
    admin = aiohttp_admin.setup(app, schema)

    assert str(admin.router["index"].url_for()) == "/admin"

    admin = aiohttp_admin.setup(app, schema, path="/another/admin")

    assert str(admin.router["index"].url_for()) == "/another/admin"
