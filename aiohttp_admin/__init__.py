import aiohttp_jinja2
import jinja2
from aiohttp import web

from .admin import (
    AdminHandler,
    setup_admin_handlers,
    setup_admin_on_rest_handlers,
    AdminOnRestHandler,
)
from .consts import PROJ_ROOT, TEMPLATE_APP_KEY, APP_KEY, TEMPLATES_ROOT
from .security import Permissions, require, authorize
from .utils import gather_template_folders


__all__ = ['AdminHandler', 'setup', 'get_admin', 'Permissions', 'require',
           'authorize', '_setup', ]
__version__ = '0.0.2'


def setup(app, admin_conf_path, *, resources, static_folder=None,
          template_folder=None, template_name=None, name=None,
          app_key=APP_KEY):

    admin = web.Application(loop=app.loop)
    app[app_key] = admin

    tf = gather_template_folders(template_folder)
    loader = jinja2.FileSystemLoader(tf)
    aiohttp_jinja2.setup(admin, loader=loader, app_key=TEMPLATE_APP_KEY)

    template_name = template_name or 'admin.html'
    admin_handler = AdminHandler(admin, resources=resources, name=name,
                                 template=template_name, loop=app.loop)

    admin['admin_handler'] = admin_handler
    admin['layout_path'] = admin_conf_path

    static_folder = static_folder or str(PROJ_ROOT / 'static')
    setup_admin_handlers(admin, admin_handler, static_folder, admin_conf_path)
    return admin


def _setup(app, *, schema,  title=None, app_key=APP_KEY, db=None):
    """Initialize the admin-on-rest admin"""

    admin = web.Application(loop=app.loop)
    app[app_key] = admin
    loader = jinja2.FileSystemLoader([TEMPLATES_ROOT, ])
    aiohttp_jinja2.setup(admin, loader=loader, app_key=TEMPLATE_APP_KEY)

    if title:
        schema.title = title

    resources = [
        init(db, info['table'], url=info['url'])
        for init, info in schema.resources
    ]

    admin_handler = AdminOnRestHandler(
        admin,
        resources=resources,
        loop=app.loop,
        schema=schema,
    )

    admin['admin_handler'] = admin_handler
    setup_admin_on_rest_handlers(admin, admin_handler)

    return admin


def get_admin(app, *, app_key=APP_KEY):
    return app.get(app_key)
