import __main__
import json
from typing import TypedDict

from aiohttp import web
from aiohttp_security import forget, remember
from pydantic import Json, parse_obj_as


class _Login(TypedDict):
    username: str
    password: str


INDEX_TEMPLATE = """<!doctype html>
<html>
<head>
    <meta charset="utf-8" />
    <link rel="icon" href="{icon}" />
    <title>{name} Admin</title>
    <script src="{js}" defer="defer"></script>
</head>
<body data-state='{state}'>
    <noscript>You need to enable JavaScript to access this page.</noscript>
    <div id="root"></div>
</body>
</html>"""


async def index(request: web.Request) -> web.Response:
    """Root page which loads react-admin."""
    static = request.app.router["static"]
    js = static.url_for(filename="admin.js")
    state = json.dumps(request.app["state"])

    # __package__ can be None, despite what the documentation claims.
    package_name = __main__.__package__ or "My"
    # Common convention is to have _app suffix for package name, so try and strip that.
    package_name = package_name.removesuffix("_app").replace("_", " ").title()
    name = request.app["state"]["view"].get("name", package_name)

    icon = request.app["state"]["view"].get("icon", static.url_for(filename="favicon.svg"))

    output = INDEX_TEMPLATE.format(name=name, icon=icon, js=js, state=state)
    return web.Response(text=output, content_type="text/html")


async def token(request: web.Request) -> web.Response:
    """Validate user credentials and log the user in."""
    data = parse_obj_as(Json[_Login], await request.read())

    check_credentials = request.app["check_credentials"]
    if not await check_credentials(data["username"], data["password"]):
        raise web.HTTPUnauthorized(text="Wrong username or password")

    response = web.Response()
    await remember(request, response, data["username"])
    return response


async def logout(request: web.Request) -> web.Response:
    """Log the user out."""
    response = web.json_response()
    await forget(request, response)
    return response
