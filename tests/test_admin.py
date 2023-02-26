from aiohttp import web

import aiohttp_admin
from _auth import DummyAuthPolicy, check_credentials, identity_callback


def test_path() -> None:
    app = web.Application()
    schema: aiohttp_admin.Schema = {"security": {"check_credentials": check_credentials,
                                                 "identity_callback": identity_callback},
                                    "resources": ()}
    admin = aiohttp_admin.setup(app, schema, DummyAuthPolicy())

    assert str(admin.router["index"].url_for()) == "/admin"

    admin = aiohttp_admin.setup(app, schema, DummyAuthPolicy(), path="/another/admin")

    assert str(admin.router["index"].url_for()) == "/another/admin"
