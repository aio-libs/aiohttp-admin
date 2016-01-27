__all__ = ['Admin']


class Admin:

    def __init__(self, app, *, url=None, static_url_path=None, loop):
        self._app = app
        self._loop = loop
        self._resources = []
        self.url = url or 'admin'
        self.static_url_path = static_url_path

    @property
    def app(self):
        return self._app

    def add_resource(self, resource):
        resource.setup(self.app, self._url)
        self._resources.append(resource)
