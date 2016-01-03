from .base import AdminIndexView
from .menu import MenuCategory, MenuView


__all__ = ['Admin']


class Admin:
    """Collection of the admin views. Also manages menu structure."""
    def __init__(self,
                 app=None,
                 name=None,
                 url=None,
                 index_view=None,
                 translations_path=None,
                 endpoint=None,
                 static_url_path=None,
                 base_template=None,
                 template_mode=None,
                 category_icon_classes=None):
        """
        Constructor.

        :param app: aiohttp application object
        :param name: Application name. Will be displayed in the main menu
            and as a page title. Defaults to "Admin"
        :param url: Base URL
        :param index_view: Home page view to use. Defaults to `AdminIndexView`.
        :param translations_path: Location of the translation message catalogs.
            By default will use the translations shipped with.
        :param endpoint: Base endpoint name for index view. If you use
            multiple instances of the `Admin` class with a single Flask
            application, you have to set a unique endpoint name for each
            instance.
        :param static_url_path: Static URL Path. If provided, this specifies
            the default path to the static url directory for all its views.
            Can be overridden in view configuration.
        :param base_template: Override base HTML template for all static
            views. Defaults to `admin/base.html`.
        :param template_mode: Base template path. Defaults to `bootstrap3`.
        :param category_icon_classes: A dict of category names as keys and
            html classes as values to be added to menu category icons.
            Example: {'Favorites': 'glyphicon glyphicon-star'}
        """
        self._app = app
        self.translations_path = translations_path
        self._views = []
        self._menu = []
        self._menu_categories = dict()
        self._menu_links = []

        if name is None:
            name = 'Admin'
        self.name = name

        self.index_view = index_view or AdminIndexView(
            endpoint=endpoint, url=url)
        self.endpoint = endpoint or self.index_view.endpoint
        self.url = url or self.index_view.url
        self.static_url_path = static_url_path
        self.base_template = base_template or 'admin/base.html'
        self.template_mode = template_mode or 'bootstrap3'
        self.category_icon_classes = category_icon_classes or dict()

        # Add predefined index view
        self.add_view(self.index_view)

    @property
    def app(self):
        return self._app

    def add_view(self, view):
        """Add a view to the collection.

        :param view: View to add.
        """
        view.add_routes(self._app, self)
        self._views.append(view)
        self._add_view_to_menu(view)

    def add_views(self, *args):
        """Add one or more views to the collection.

        Examples::

            admin.add_views(view1)
            admin.add_views(view1, view2, view3, view4)
            admin.add_views(*my_list)

        :param args: Argument list including the views to add.
        """
        for view in args:
            self.add_view(view)

    def add_link(self, link):
        """Add link to menu links collection.

        :param link: Link to add.
        """
        # attach admin instance to this link/menu
        link.admin = self
        if link.category:
            self._add_menu_item(link, link.category)
        else:
            self._menu_links.append(link)

    def add_links(self, *args):
        """Add one or more links to the menu links collection.

        Examples::

            admin.add_links(link1)
            admin.add_links(link1, link2, link3, link4)
            admin.add_links(*my_list)

        :param args: Argument list including the links to add.
        """
        for link in args:
            self.add_link(link)

    def _add_menu_item(self, menu_item, target_category):
        if target_category:
            # TODO: refactor next line and make sure that this line is
            # working
            cat_text = target_category

            category = self._menu_categories.get(cat_text)

            # create a new menu category if one does not exist already
            if category is None:
                category = MenuCategory(target_category)
                category.class_name = self.category_icon_classes.get(cat_text)
                self._menu_categories[cat_text] = category

                self._menu.append(category)

            category.add_child(menu_item)
        else:
            self._menu.append(menu_item)

    def _add_view_to_menu(self, view):
        """Add a view to the menu tree

        :param view: View to add
        """
        self._add_menu_item(MenuView(view.name, view), view.category)

    def get_category_menu_item(self, name):
        return self._menu_categories.get(name)

    def menu(self):
        """Return the menu hierarchy."""
        return self._menu

    def menu_links(self):
        """Return menu links."""
        return self._menu_links
