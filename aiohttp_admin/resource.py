import abc
from abc import abstractmethod


class AbstractResource(metaclass=abc.ABCMeta):

    def __init__(self, url=None):
        class_name = self.__class__.__name__.lower()
        self._url = url or class_name

    @abstractmethod
    async def list(self, request):
        pass

    @abstractmethod
    async def detail(self, request):
        pass

    @abstractmethod
    async def create(self, request):
        pass

    @abstractmethod
    async def update(self, request):
        pass

    @abstractmethod
    async def delete(self, request):
        pass

    def setup(self, app, base_url):
        url = '{}/{}'.format(base_url, self._url)
        url_id = url + '/{entity_id}'
        add_route = app.router.add_route
        add_route('GET', url, self.list)
        add_route('GET', url_id, self.detail)
        add_route('POST', url, self.create)
        add_route('PUT', url_id, self.update)
        add_route('DELETE', url_id, self.delete)
