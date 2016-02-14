import aiohttp_jinja2
import jinja2


from .admin import Admin, index_handler
from .consts import TEMPLATES_ROOT, PROJ_ROOT, TEMPLATE_APP_KEY, APP_KEY


__all__ = ['Admin', 'setup']
__version__ = '0.0.1'


def gather_tempalte_folder(template_folder):
    # gather template folders: default and provided
    if not isinstance(template_folder, list):
        template_folder = [template_folder]
    template_root = str(TEMPLATES_ROOT)
    if template_folder is None:
        template_folders = [template_root]
    else:
        template_folders = [template_root] + template_folder
    return template_folders


def setup(app, admin_conf_path, url=None, static_url=None,
          template_folder=None):
    loop = app.loop

    # setup routes
    url = url or '/admin'
    static_url = static_url or '/admin/static'

    app.router.add_route('GET', url, index_handler, name='admin.index')
    app.router.add_static(static_url,
                          path=str(PROJ_ROOT / 'static'),
                          name='admin.static')
    app.router.add_static('/admin/config',
                          path=admin_conf_path,
                          name='admin.config')

    # init aiohttp_jinja plugin
    tf = gather_tempalte_folder(template_folder)
    loader = jinja2.FileSystemLoader(tf)
    aiohttp_jinja2.setup(app, loader=loader, app_key=TEMPLATE_APP_KEY)

    admin = Admin(app, url=url, loop=loop)
    # add support for multiple admins sites
    app[APP_KEY] = admin
    return admin
