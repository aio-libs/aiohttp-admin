import pathlib
import aiohttp_jinja2
import jinja2


from .admin import Admin


__all__ = ['Admin', 'setup']
__version__ = '0.0.1'


APP_KEY = 'aiohttp_admin'
TEMPLATES_ROOT = pathlib.Path(__file__).parent / 'templates'
PROJ_ROOT = pathlib.Path(__file__).parent
TEMPLATE_APP_KEY = 'aiohttp_admin_templates'


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


def setup(app, url=None, static_url_path=None, template_folder=None):
    loop = app.loop
    url = url or 'admin'
    static_url_path = static_url_path or '/admin/static'
    app.router.add_static(static_url_path,
                          path=str(PROJ_ROOT / 'static'),
                          name='admin.static')
    tf = gather_tempalte_folder(template_folder)

    # init aiohttp_jinja plugin
    loader = jinja2.FileSystemLoader(tf)
    aiohttp_jinja2.setup(app, loader=loader, app_key=TEMPLATE_APP_KEY)

    admin = Admin(app, url=url, loop=loop)
    # add support for multiple admins sites
    app[APP_KEY] = admin
    return admin
