from abc import abstractmethod, ABCMeta

from .security import Permissions, require
from .utils import json_response, validate_query


class AbstractResource(metaclass=ABCMeta):

    def __init__(self, *, primary_key, resource_name=None):
        class_name = self.__class__.__name__.lower()
        self._resource_name = resource_name or class_name
        self._primary_key = primary_key

    @property
    def primary_key(self):
        return self._primary_key

    @abstractmethod
    async def list(self, request):  # pragma: no cover
        await require(request, Permissions.view)
        q = validate_query(request.GET)
        assert q

        # total number of results should be supplied in separate
        headers = {'X-Total-Count': str(0)}
        return json_response({}, headers=headers)

    @abstractmethod
    async def detail(self, request):  # pragma: no cover
        await require(request, Permissions.view)
        entity_id = request.match_info['entity_id']
        assert entity_id
        return json_response({})

    @abstractmethod
    async def create(self, request):  # pragma: no cover
        await require(request, Permissions.add)
        return json_response({})

    @abstractmethod
    async def update(self, request):  # pragma: no cover
        await require(request, Permissions.edit)
        entity_id = request.match_info['entity_id']
        assert entity_id
        return json_response({})

    @abstractmethod
    async def delete(self, request):  # pragma: no cover
        await require(request, Permissions.delete)
        entity_id = request.match_info['entity_id']
        assert entity_id
        return json_response({})

    def setup(self, app, base_url):
        url = str(base_url / self._resource_name)
        url_id = url + '/{entity_id}'
        add_route = app.router.add_route
        add_route('GET', url, self.list)
        add_route('GET', url_id, self.detail)
        add_route('POST', url, self.create)
        add_route('PUT', url_id, self.update)
        add_route('DELETE', url_id, self.delete)
