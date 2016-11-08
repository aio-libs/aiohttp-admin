import aiohttp_jinja2
import jinja2
from aiohttp import web


from .admin import AdminHandler, setup_admin_handlers
from .consts import PROJ_ROOT, TEMPLATE_APP_KEY, APP_KEY
from .security import Permissions, require, authorize
from .utils import gather_template_folders


__all__ = ['AdminHandler', 'setup', 'get_admin', 'Permissions', 'require',
           'authorize']
__version__ = '0.0.1'


def setup(app, admin_conf_path, *, resources, static_url=None,
          static_folder=None, template_folder=None, template_name=None,
          name=None, app_key=APP_KEY):

    admin = web.Application(loop=app.loop)
    app[app_key] = admin

    # init aiohttp_jinja plugin
    tf = gather_template_folders(template_folder)
    loader = jinja2.FileSystemLoader(tf)
    aiohttp_jinja2.setup(admin, loader=loader, app_key=TEMPLATE_APP_KEY)

    template_name = template_name or 'admin.html'
    admin_handler = AdminHandler(admin, name=name, template=template_name,
                                 loop=app.loop)
    for r in resources:
        admin_handler.add_resource(r)

    admin['admin_handler'] = admin_handler
    # TODO: fix this hack
    admin._resources = admin_handler._resources

    static_url = static_url or '/admin/static'
    static_folder = static_folder or str(PROJ_ROOT / 'static')
    setup_admin_handlers(admin, admin_handler, static_url, static_folder,
                         admin_conf_path)
    return admin


def get_admin(app, *, app_key=APP_KEY):
    return app.get(app_key)
