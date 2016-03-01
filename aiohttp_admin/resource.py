import abc
from abc import abstractmethod

from .utils import json_response, validate_query


class AbstractResource(metaclass=abc.ABCMeta):

    def __init__(self, url=None):
        class_name = self.__class__.__name__.lower()
        self._url = url or class_name

    @abstractmethod
    async def list(self, request):  # pragma: no cover
        q = validate_query(request.GET)
        assert q
        return json_response({})

    @abstractmethod
    async def detail(self, request):  # pragma: no cover
        entity_id = request.match_info['entity_id']
        assert entity_id
        return json_response({})

    @abstractmethod
    async def create(self, request):  # pragma: no cover
        return json_response({})

    @abstractmethod
    async def update(self, request):  # pragma: no cover
        entity_id = request.match_info['entity_id']
        assert entity_id
        return json_response({})

    @abstractmethod
    async def delete(self, request):  # pragma: no cover
        entity_id = request.match_info['entity_id']
        assert entity_id
        return json_response({})

    def setup(self, app, base_url):
        url = '{}/{}'.format(base_url, self._url)
        url_id = url + '/{entity_id}'
        add_route = app.router.add_route
        add_route('GET', url, self.list)
        add_route('GET', url_id, self.detail)
        add_route('POST', url, self.create)
        add_route('PUT', url_id, self.update)
        add_route('DELETE', url_id, self.delete)
