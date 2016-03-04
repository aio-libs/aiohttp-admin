import aiohttp_jinja2
import jinja2


from .admin import Admin, get_admin
from .consts import PROJ_ROOT, TEMPLATE_APP_KEY, APP_KEY
from .utils import gather_template_folders


__all__ = ['Admin', 'setup', 'get_admin']
__version__ = '0.0.1'


def setup(app, admin_conf_path=None, url=None, static_url=None,
          template_folder=None, name=None, app_key=APP_KEY):
    loop = app.loop

    admin = Admin(app, url=url, name=name, loop=loop)
    # add support for multiple admins sites
    app[APP_KEY] = admin

    # setup routes
    url = url or '/admin'
    static_url = static_url or '/admin/static'
    config_url = '/admin/static/js/config.js'

    app.router.add_route('GET', url, admin.index_handler, name='admin.index')
    if admin_conf_path:
        app.router.add_static(static_url,
                              path=admin_conf_path,
                              name='admin.config')
    else:
        app.router.add_route('GET',
                             config_url,
                             admin.config_handler,
                             name='admin.config')
    app.router.add_static(static_url,
                          path=str(PROJ_ROOT / 'static'),
                          name='admin.static')

    # init aiohttp_jinja plugin
    tf = gather_template_folders(template_folder)
    loader = jinja2.FileSystemLoader(tf)
    aiohttp_jinja2.setup(app, loader=loader, app_key=TEMPLATE_APP_KEY)

    return admin
