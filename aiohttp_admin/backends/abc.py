import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from functools import cached_property, partial
from typing import Any, Literal, TypedDict, Union

from aiohttp import web
from aiohttp_security import check_permission
from pydantic import Json, parse_obj_as

Record = dict[str, object]


class Encoder(json.JSONEncoder):
    def default(self, o: object) -> Any:
        if isinstance(o, datetime):
            return str(o)
        if isinstance(o, Enum):
            return o.value

        return super().default(o)


json_response = partial(web.json_response, dumps=partial(json.dumps, cls=Encoder))


class Permissions(str, Enum):
    view = "admin.view"
    edit = "admin.edit"
    add = "admin.add"
    delete = "admin.delete"


class FieldState(TypedDict):
    type: str
    props: dict[str, Union[int, str]]


class InputState(FieldState):
    # Whether to show this input in the create form.
    show_create: bool


class _Pagination(TypedDict):
    page: int
    perPage: int


class _Sort(TypedDict):
    field: str
    order: Literal["ASC", "DESC"]


class _Params(TypedDict, total=False):
    meta: dict[str, object]


class GetListParams(_Params):
    pagination: Json[_Pagination]
    sort: Json[_Sort]
    filter: Json[dict[str, object]]


class GetOneParams(_Params):
    id: Union[int, str]


class GetManyParams(_Params):
    ids: Json[list[Union[int, str]]]


class CreateParams(_Params):
    data: Json[Record]


class UpdateParams(_Params):
    id: Union[int, str]
    data: Json[Record]
    previousData: Json[Record]


class DeleteParams(_Params):
    id: Union[int, str]
    previousData: Json[Record]


class DeleteManyParams(_Params):
    ids: Json[list[Union[int, str]]]


class AbstractAdminResource(ABC):
    name: str
    fields: dict[str, FieldState]
    inputs: dict[str, InputState]
    repr_field: str

    @abstractmethod
    async def get_list(self, params: GetListParams) -> tuple[list[Record], int]:
        """Return list of records and total count available (when not paginating)."""

    @abstractmethod
    async def get_one(self, params: GetOneParams) -> Record:
        """Return the matching record."""

    @abstractmethod
    async def get_many(self, params: GetManyParams) -> list[Record]:
        """Return the matching records."""

    @abstractmethod
    async def update(self, params: UpdateParams) -> Record:
        """Update the record and return the updated record."""

    @abstractmethod
    async def create(self, params: CreateParams) -> Record:
        """Create a new record and return the created record."""

    @abstractmethod
    async def delete(self, params: DeleteParams) -> Record:
        """Delete a record and return the deleted record."""

    @abstractmethod
    async def delete_many(self, params: DeleteManyParams) -> list[Union[int, str]]:
        """Delete the matching records and return their IDs."""

    # https://marmelab.com/react-admin/DataProviderWriting.html

    async def _get_list(self, request: web.Request) -> web.Response:
        await check_permission(request, Permissions.view)
        query = parse_obj_as(GetListParams, request.query)

        results, total = await self.get_list(query)
        return json_response({"data": results, "total": total})

    async def _get_one(self, request: web.Request) -> web.Response:
        await check_permission(request, Permissions.view)
        query = parse_obj_as(GetOneParams, request.query)

        result = await self.get_one(query)
        return json_response({"data": result})

    async def _get_many(self, request: web.Request) -> web.Response:
        await check_permission(request, Permissions.view)
        query = parse_obj_as(GetManyParams, request.query)

        results = await self.get_many(query)
        return json_response({"data": results})

    async def _create(self, request: web.Request) -> web.Response:
        await check_permission(request, Permissions.add)
        query = parse_obj_as(CreateParams, request.query)

        result = await self.create(query)
        return json_response({"data": result})

    async def _update(self, request: web.Request) -> web.Response:
        await check_permission(request, Permissions.edit)
        query = parse_obj_as(UpdateParams, request.query)

        result = await self.update(query)
        return json_response({"data": result})

    async def _delete(self, request: web.Request) -> web.Response:
        await check_permission(request, Permissions.delete)
        query = parse_obj_as(DeleteParams, request.query)

        result = await self.delete(query)
        return json_response({"data": result})

    async def _delete_many(self, request: web.Request) -> web.Response:
        await check_permission(request, Permissions.delete)
        query = parse_obj_as(DeleteManyParams, request.query)

        ids = await self.delete_many(query)
        return json_response({"data": ids})

    @cached_property
    def routes(self) -> tuple[web.RouteDef, ...]:
        """Routes to act on this resource.

        Every route returned must have a name.
        """
        url = "/" + self.name
        return (
            web.get(url + "/list", self._get_list, name=self.name + "_get_list"),
            web.get(url + "/one", self._get_one, name=self.name + "_get_one"),
            web.get(url, self._get_many, name=self.name + "_get_many"),
            web.post(url, self._create, name=self.name + "_create"),
            web.put(url + "/update", self._update, name=self.name + "_update"),
            web.delete(url + "/one", self._delete, name=self.name + "_delete"),
            web.delete(url, self._delete_many, name=self.name + "_delete_many")
        )
