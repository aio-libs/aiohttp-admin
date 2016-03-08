import aiohttp_jinja2
import jinja2


from .admin import Admin, get_admin
from .consts import PROJ_ROOT, TEMPLATE_APP_KEY, APP_KEY
from .utils import gather_template_folders


__all__ = ['Admin', 'setup', 'get_admin']
__version__ = '0.0.1'


def setup(app, admin_conf_path, *, url=None, static_url=None,
          static_folder=None, template_folder=None, template_name=None,
          name=None, app_key=APP_KEY):
    loop = app.loop
    template_name = template_name or 'admin.html'
    admin = Admin(app, url=url, name=name, template=template_name, loop=loop)
    # add support for multiple admins sites
    app[app_key] = admin

    # setup routes
    url = url or '/admin'
    static_url = static_url or '/admin/static'
    static_folder = static_folder or str(PROJ_ROOT / 'static')

    r = app.router
    r.add_route('GET', url, admin.index_handler, name='admin.index')
    r.add_static(static_url, path=static_folder, name='admin.static')
    r.add_static('/admin/config', path=admin_conf_path, name='admin.config')

    # init aiohttp_jinja plugin
    tf = gather_template_folders(template_folder)
    loader = jinja2.FileSystemLoader(tf)
    aiohttp_jinja2.setup(app, loader=loader, app_key=TEMPLATE_APP_KEY)

    return admin
