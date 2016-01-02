import aiohttp_jinja2
import jinja2


from .admin import Admin
from .base import BaseView
from .consts import APP_KEY, TEMPLATE_APP_KEY
from .consts import PROJ_ROOT, TEMPLATES_ROOT


__all__ = ['Admin', 'BaseView', 'setup']
__version__ = '0.0.1'


def setup(app, name=None, url=None, index_view=None,
          translations_path=None, endpoint=None, static_url_path=None,
          base_template=None, template_mode=None, category_icon_classes=None):

    app.router.add_static('/static/admin',
                          path=str(PROJ_ROOT / 'static'),
                          name='admin.static')

    loader = jinja2.FileSystemLoader([str(TEMPLATES_ROOT)])
    aiohttp_jinja2.setup(app, loader=loader, app_key=TEMPLATE_APP_KEY)

    admin = Admin(app, name=name, url=url, index_view=index_view,
                  translations_path=translations_path, endpoint=endpoint,
                  static_url_path=static_url_path,
                  base_template=base_template, template_mode=template_mode,
                  category_icon_classes=category_icon_classes)
    app[APP_KEY] = admin
    return admin
