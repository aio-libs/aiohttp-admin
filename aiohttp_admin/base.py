import aiohttp_jinja2
from aiohttp import web

from . import babel
from . import helpers as h
from .consts import TEMPLATE_APP_KEY


class BaseView:

    def __init__(self, name=None, category=None, endpoint=None, url=None,
                 static_folder=None, static_url_path=None,
                 menu_class_name=None, menu_icon_type=None,
                 menu_icon_value=None):
        """Constructor.

        :param name: Name of this view. If not provided, will default to the
            class name.
        :param category: View category. If not provided, this view will be
            shown as a top-level menu item. Otherwise, it will be in a submenu.
        :param endpoint: Base endpoint name for the view. For example, if
            there's a view method called "index" and endpoint is set to
            "myadmin", you can use `url_for('myadmin.index')` to get the URL
            to the view method. Defaults to the class name in lower case.
        :param url: Base URL. If provided, affects how URLs are generated.
            For example, if the url parameter is "test", the resulting URL
            will look like "/admin/test/". If not provided, will use endpoint
            as a base url. However, if URL starts with '/', absolute path
            is assumed and '/admin/' prefix won't be applied.
        :param static_url_path: Static URL Path. If provided, this specifies
            the path to the static url directory.
        :param menu_class_name: Optional class name for the menu item.
        :param menu_icon_type: Optional icon. Possible icon types:
             - `aiohttp_admin.consts.ICON_TYPE_GLYPH` - Bootstrap glyph icon
             - `aiohttp_admin.consts.ICON_TYPE_FONT_AWESOME` Font Awesome icon
             - `aiohttp_admin.consts.ICON_TYPE_IMAGE` - Image relative to
                static directory
             - `aiohttp_admin.consts.ICON_TYPE_IMAGE_URL` - Image with full URL
        :param menu_icon_value: Icon glyph name or URL, depending on
            `menu_icon_type` setting
        """
        self.name = name
        self.category = category
        self.endpoint = self._get_endpoint(endpoint)
        self.url = url
        self.static_folder = static_folder
        self.static_url_path = static_url_path
        self.menu = None

        self.menu_class_name = menu_class_name
        self.menu_icon_type = menu_icon_type
        self.menu_icon_value = menu_icon_value

        # Initialized from create_blueprint
        self.admin = None
        self.blueprint = None

        # TODO: figure out what to do with default  views
        # Default view
        # if self._default_view is None:
        #    raise Exception(u'Attempted to instantiate admin
        # view %s without default view' % self.__class__.__name__)

    def _get_endpoint(self, endpoint):
        """Generate Flask endpoint name. By default converts class name to
        lower case if endpoint is not explicitly provided.
        """
        if endpoint:
            return endpoint
        return self.__class__.__name__.lower()

    def _get_view_url(self, admin, url):
        """Generate URL for the view. Override to change default behavior."""
        if url is None:
            if admin.url != '/':
                url = '%s/%s' % (admin.url, self.endpoint)
            else:
                if self == admin.index_view:
                    url = '/'
                else:
                    url = '/%s' % self.endpoint
        else:
            if not url.startswith('/'):
                url = '%s/%s' % (admin.url, url)

        return url

    def add_routes(self, app, admin):
        # Store admin instanced
        self.admin = admin

        # If the static_url_path is not provided, use the admin's
        if not self.static_url_path:
            self.static_url_path = admin.static_url_path

        # Generate URL
        self.url = self._get_view_url(admin, self.url)

        # If we're working from the root of the site, set prefix to None
        if self.url == '/':
            self.url = None
            # prevent admin static files from conflicting with default
            # static files
            if not self.static_url_path:
                self.static_folder = 'static'
                self.static_url_path = '/static/admin'

        # If name is not povided, use capitalized endpoint name
        if self.name is None:
            self.name = self._prettify_class_name(self.__class__.__name__)

        add_route = app.router.add_route
        for method, url, handler, name in self.urls():
            full_url = self.url + url
            # TODO: fix this, decorator around will kill this logic
            name = handler.__name__
            n = '{endpoint}.{name}'.format(endpoint=self.endpoint, name=name)
            add_route(method, full_url, handler, name=n)
            if url == '/':
                self._default_view = name

    def render(self, request, template, **kwargs):
        """Render template

        :param template: Template path to render
        :param kwargs: Template arguments
        """
        # Store self as admin_view
        kwargs['admin_view'] = self
        base_template = self.admin.base_template or 'admin/base.html'
        kwargs['admin_base_template'] = base_template

        # Provide i18n support even if flask-babel is not installed
        # or enabled.
        kwargs['_gettext'] = babel.gettext
        kwargs['_ngettext'] = babel.ngettext
        kwargs['h'] = h

        # Expose get_url helper
        kwargs['get_url'] = self.get_url

        # Expose config info
        # TODO: do wen need expose config?
        # kwargs['config'] = current_app.config

        return aiohttp_jinja2.render_template(template, request, kwargs,
                                              app_key=TEMPLATE_APP_KEY)

    def _prettify_class_name(self, name):
        """Split words in PascalCase string into separate words.

        :param name: String to prettify
        """
        return h.prettify_class_name(name)

    def is_visible(self):
        """Override this method if you want dynamically hide or show
        administrative views from Flask-Admin menu structure

        By default, item is visible in menu.

        Please note that item should be both visible and accessible to be
        displayed in menu.
        """
        return True

    def is_accessible(self):
        """Override this method to add permission checks.

        Flask-Admin does not make any assumptions about the authentication
        system used in your application, so it is up to you to implement it.

        By default, it will allow access for everyone.
        """
        return True

    def _handle_view(self, name, **kwargs):
        """This method will be executed before calling any view method.

        It will execute the ``inaccessible_callback`` if the view is not
        accessible.

        :param name: View function name
        :param kwargs: View function arguments
        """
        if not self.is_accessible():
            return self.inaccessible_callback(name, **kwargs)

    def inaccessible_callback(self, name, **kwargs):
        """Handle the response to inaccessible views.

            By default, it throw HTTP 403 error. Override this method to
            customize the behaviour.
        """
        raise web.Response(status=403)

    def get_url(self, name, **kwargs):
        """Generate URL for the endpoint. If you want to customize URL
        generation logic (persist some query string argument, for example),
        this is right place to do it.

        :param endpoint: endpoint name
        :param kwargs: Arguments for `url_for`
        """
        if name.startswith('.'):
            name = '{}{}'.format(self.endpoint, name)

        router = self.admin.app.router
        return router[name].url(**kwargs)


class AdminIndexView(BaseView):
    """Default administrative interface index page when visiting the
    ``/admin/`` URL.

    Default values for the index page are:

    * If a name is not provided, 'Home' will be used.
    * If an endpoint is not provided, will default to ``admin``
    * Default URL route is ``/admin``.
    * Automatically associates with static folder.
    * Default template is ``admin/index.html``
    """
    def __init__(self, name=None, category=None,
                 endpoint=None, url=None,
                 template='admin/index.html',
                 menu_class_name=None,
                 menu_icon_type=None,
                 menu_icon_value=None):

        super().__init__(name or babel.lazy_gettext('Home'),
                         category,
                         endpoint or 'admin',
                         url or '/admin',
                         'static',
                         menu_class_name=menu_class_name,
                         menu_icon_type=menu_icon_type,
                         menu_icon_value=menu_icon_value)
        self._template = template
        self.base_template = None

    async def index(self, request):
        return self.render(request, self._template)

    def urls(self):
        return [('GET', '/', self.index, 'index')]
