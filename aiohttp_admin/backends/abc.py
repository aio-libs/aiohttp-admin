import asyncio
import json
import warnings
from abc import ABC, abstractmethod
from datetime import date, datetime
from enum import Enum
from functools import cached_property, partial
from types import MappingProxyType
from typing import Any, Literal, Optional, TypedDict, Union

from aiohttp import web
from aiohttp_security import check_permission, permits
from pydantic import Json, parse_obj_as

from ..security import permissions_as_dict
from ..types import FieldState, InputState

Record = dict[str, object]

INPUT_TYPES = MappingProxyType({
    "BooleanInput": bool,
    "DateInput": date,
    "DateTimeInput": datetime,
    "NumberInput": float
})


class Encoder(json.JSONEncoder):
    def default(self, o: object) -> Any:
        if isinstance(o, date):
            return str(o)
        if isinstance(o, Enum):
            return o.value

        return super().default(o)


json_response = partial(web.json_response, dumps=partial(json.dumps, cls=Encoder))


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


class UpdateManyParams(_Params):
    ids: Json[list[Union[int, str]]]
    data: Json[Record]


class DeleteParams(_Params):
    id: Union[int, str]
    previousData: Json[Record]


class DeleteManyParams(_Params):
    ids: Json[list[Union[int, str]]]


class AbstractAdminResource(ABC):
    name: str
    fields: dict[str, FieldState]
    inputs: dict[str, InputState]
    primary_key: str

    def __init__(self) -> None:
        if "id" in self.fields and self.primary_key != "id":
            warnings.warn("A non-PK 'id' column is likely to break the admin.", stacklevel=2)

        d = {k: INPUT_TYPES.get(v["type"], str) for k, v in self.inputs.items()}
        # For runtime type checking only.
        self._record_type = TypedDict("RecordType", d, total=False)  # type: ignore[misc]

    async def filter_by_permissions(self, request: web.Request, perm_type: str,
                                    record: Record, original: Optional[Record] = None) -> Record:
        """Return a filtered record containing permissible fields only."""
        return {k: v for k, v in record.items()
                if await permits(request, f"admin.{self.name}.{k}.{perm_type}",
                                 context=(request, original or record))}

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
    async def update_many(self, params: UpdateManyParams) -> list[Union[int, str]]:
        """Update multiple records and return the IDs of updated records."""

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
        await check_permission(request, f"admin.{self.name}.view", context=(request, None))
        query = parse_obj_as(GetListParams, request.query)

        # When sort order refers to "id", this should be translated to primary key.
        if query["sort"]["field"] == "id":
            query["sort"]["field"] = self.primary_key

        # Add filters from advanced permissions.
        # The permissions will be cached on the request from a previous permissions check.
        permissions = permissions_as_dict(request["aiohttpadmin_permissions"])
        filters = permissions.get(f"admin.{self.name}.view",
                                  permissions.get(f"admin.{self.name}.*", {}))
        for k, v in filters.items():
            query["filter"][k] = v

        results, total = await self.get_list(query)
        results = [await self.filter_by_permissions(request, "view", r) for r in results]
        results = [r for r in results if await permits(request, f"admin.{self.name}.view",
                                                       context=(request, r))]
        # We need to set "id" for react-admin (in case there is no "id" primary key).
        for r in results:
            r["id"] = r[self.primary_key]
        return json_response({"data": results, "total": total})

    async def _get_one(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.view", context=(request, None))
        query = parse_obj_as(GetOneParams, request.query)

        result = await self.get_one(query)
        if not await permits(request, f"admin.{self.name}.view", context=(request, result)):
            raise web.HTTPForbidden()
        result = await self.filter_by_permissions(request, "view", result)
        result["id"] = result[self.primary_key]
        return json_response({"data": result})

    async def _get_many(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.view", context=(request, None))
        query = parse_obj_as(GetManyParams, request.query)

        results = await self.get_many(query)
        results = [await self.filter_by_permissions(request, "view", r) for r in results
                   if await permits(request, f"admin.{self.name}.view", context=(request, r))]
        for r in results:
            r["id"] = r[self.primary_key]
        return json_response({"data": results})

    async def _create(self, request: web.Request) -> web.Response:
        query = parse_obj_as(CreateParams, request.query)
        # TODO(Pydantic): Dissallow extra arguments
        for k in query["data"]:
            if k not in self.inputs and k != "id":
                raise web.HTTPBadRequest(reason=f"Invalid field '{k}'")
        query["data"] = parse_obj_as(self._record_type, query["data"])
        await check_permission(request, f"admin.{self.name}.add", context=(request, query["data"]))
        for k, v in query["data"].items():
            if v is not None:
                await check_permission(request, f"admin.{self.name}.{k}.add",
                                       context=(request, query["data"]))

        result = await self.create(query)
        result = await self.filter_by_permissions(request, "view", result)
        result["id"] = result[self.primary_key]
        return json_response({"data": result})

    async def _update(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.edit", context=(request, None))
        query = parse_obj_as(UpdateParams, request.query)
        # TODO(Pydantic): Dissallow extra arguments
        for k in query["data"]:
            if k not in self.inputs and k != "id":
                raise web.HTTPBadRequest(reason=f"Invalid field '{k}'")
        query["data"] = parse_obj_as(self._record_type, query["data"])
        query["previousData"] = parse_obj_as(self._record_type, query["previousData"])

        if self.primary_key != "id":
            query["data"].pop("id", None)

        # Check original record is allowed by permission filters.
        original = await self.get_one({"id": query["id"]})
        if not await permits(request, f"admin.{self.name}.edit", context=(request, original)):
            raise web.HTTPForbidden()

        # Filter rather than forbid because react-admin still sends fields without an
        # input component. The query may not be the complete dict though, so we must
        # pass original for testing.
        query["data"] = await self.filter_by_permissions(request, "edit", query["data"], original)
        # Check new values are allowed by permission filters.
        if not await permits(request, f"admin.{self.name}.edit", context=(request, query["data"])):
            raise web.HTTPForbidden()

        if not query["data"]:
            raise web.HTTPBadRequest(reason="No allowed fields to change.")

        result = await self.update(query)
        result = await self.filter_by_permissions(request, "view", result)
        result["id"] = result[self.primary_key]
        return json_response({"data": result})

    async def _update_many(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.edit", context=(request, None))
        query = parse_obj_as(UpdateManyParams, request.query)
        # TODO(Pydantic): Dissallow extra arguments
        for k in query["data"]:
            if k not in self.inputs and k != "id":
                raise web.HTTPBadRequest(reason=f"Invalid field '{k}'")
        query["data"] = parse_obj_as(self._record_type, query["data"])

        # Check original records are allowed by permission filters.
        originals = await self.get_many({"ids": query["ids"]})
        allowed = (permits(request, f"admin.{self.name}.edit", context=(request, r))
                   for r in originals)
        allowed_f = (permits(request, f"admin.{self.name}.{k}.edit", context=(request, r))
                     for r in originals for k in query["data"])
        if not all(await asyncio.gather(*allowed, *allowed_f)):
            raise web.HTTPForbidden()
        # Check new values are allowed by permission filters.
        if not await permits(request, f"admin.{self.name}.edit", context=(request, query["data"])):
            raise web.HTTPForbidden()

        ids = await self.update_many(query)
        return json_response({"data": ids})

    async def _delete(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.delete", context=(request, None))
        query = parse_obj_as(DeleteParams, request.query)
        query["previousData"] = parse_obj_as(self._record_type, query["previousData"])

        original = await self.get_one({"id": query["id"]})
        if not await permits(request, f"admin.{self.name}.delete", context=(request, original)):
            raise web.HTTPForbidden()

        result = await self.delete(query)
        result = await self.filter_by_permissions(request, "view", result)
        result["id"] = result[self.primary_key]
        return json_response({"data": result})

    async def _delete_many(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.delete", context=(request, None))
        query = parse_obj_as(DeleteManyParams, request.query)

        originals = await self.get_many(query)
        allowed = await asyncio.gather(*(permits(request, f"admin.{self.name}.delete",
                                                 context=(request, r)) for r in originals))
        if not all(allowed):
            raise web.HTTPForbidden()

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
            web.put(url + "/update_many", self._update_many, name=self.name + "_update_many"),
            web.delete(url + "/one", self._delete, name=self.name + "_delete"),
            web.delete(url, self._delete_many, name=self.name + "_delete_many")
        )
