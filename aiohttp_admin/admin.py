__all__ = ['Admin', 'admin_middleware_factory']


async def admin_middleware_factory(app, handler):
    async def admin_middleware(request):
        try:
            response = await handler(request)
        except Exception as e:
            raise e
        return response

    return admin_middleware


class Admin:

    def __init__(self, app, *, url=None, static_url_path=None, loop):
        self._app = app
        self._loop = loop
        self._resources = []
        self._url = url or 'admin'
        self.static_url_path = static_url_path

    @property
    def app(self):
        return self._app

    def add_resource(self, resource):
        resource.setup(self.app, self._url)
        self._resources.append(resource)
