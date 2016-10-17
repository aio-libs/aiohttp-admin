import aiohttp_jinja2
import jinja2
from yarl import URL


from .admin import Admin, get_admin, setup_admin_handlers
from .consts import PROJ_ROOT, TEMPLATE_APP_KEY, APP_KEY
from .security import Permissions, require, authorize
from .utils import gather_template_folders


__all__ = ['Admin', 'setup', 'get_admin', 'Permissions', 'require',
           'authorize']
__version__ = '0.0.1'


def setup(app, admin_conf_path, *, url=None, static_url=None,
          static_folder=None, template_folder=None, template_name=None,
          name=None, app_key=APP_KEY):

    # init aiohttp_jinja plugin
    tf = gather_template_folders(template_folder)
    loader = jinja2.FileSystemLoader(tf)
    aiohttp_jinja2.setup(app, loader=loader, app_key=TEMPLATE_APP_KEY)

    template_name = template_name or 'admin.html'
    admin = Admin(app, url=url, name=name, template=template_name,
                  loop=app.loop)

    # TODO: add support for multiple admins sites
    app[app_key] = admin

    # setup admin routes
    url = URL(url or '/admin')
    static_url = static_url or '/admin/static'
    static_folder = static_folder or str(PROJ_ROOT / 'static')
    setup_admin_handlers(admin, url, static_url, static_folder,
                         admin_conf_path)
    return admin
