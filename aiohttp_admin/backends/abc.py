import asyncio
import json
import sys
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date, datetime, time
from enum import Enum
from functools import cached_property, partial
from types import MappingProxyType
from typing import Any, Generic, Literal, Optional, TypeVar, final

from aiohttp import web
from aiohttp_security import check_permission, permits
from pydantic import Json

from ..security import check, permissions_as_dict
from ..types import ComponentState, InputState, fk, resources_key

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

_ID = TypeVar("_ID", bound=tuple[object, ...])
Record = dict[str, object]
Meta = Optional[dict[str, object]]

INPUT_TYPES = MappingProxyType({
    "BooleanInput": bool,
    "DateInput": date,
    "DateTimeInput": datetime,
    "NumberInput": float,
    "TimeInput": time
})


class Encoder(json.JSONEncoder):
    def default(self, o: object) -> Any:
        if isinstance(o, (date, time)):
            return str(o)
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, bytes):
            return o.decode(errors="replace")

        return super().default(o)


json_response = partial(web.json_response, dumps=partial(json.dumps, cls=Encoder))


class APIRecord(TypedDict):
    id: str
    data: Record


class _Pagination(TypedDict):
    page: int
    perPage: int


class _Sort(TypedDict):
    field: str
    order: Literal["ASC", "DESC"]


class _Params(TypedDict, total=False):
    meta: Meta


class GetListParams(_Params):
    pagination: Json[_Pagination]
    sort: Json[_Sort]
    filter: Json[dict[str, object]]


class GetOneParams(_Params):
    id: str


class GetManyParams(_Params):
    ids: Json[tuple[str, ...]]


class GetManyRefAPIParams(_Params):
    target: str
    id: str
    pagination: Json[_Pagination]
    sort: Json[_Sort]
    filter: Json[dict[str, object]]


class GetManyRefParams(_Params):
    target: tuple[str, ...]
    id: tuple[object, ...]
    pagination: Json[_Pagination]
    sort: Json[_Sort]
    filter: Json[dict[str, object]]


class _CreateData(TypedDict):
    """Id will not be included for create calls."""
    data: Record


class CreateParams(_Params):
    data: Json[_CreateData]


class UpdateParams(_Params):
    id: str
    data: Json[APIRecord]
    previousData: Json[APIRecord]


class UpdateManyParams(_Params):
    ids: Json[tuple[str, ...]]
    data: Json[Record]


class DeleteParams(_Params):
    id: str
    previousData: Json[APIRecord]


class DeleteManyParams(_Params):
    ids: Json[tuple[str, ...]]


class _ListQuery(TypedDict):
    sort: _Sort
    filter: dict[str, object]


class AbstractAdminResource(ABC, Generic[_ID]):
    name: str
    fields: dict[str, ComponentState]
    inputs: dict[str, InputState]
    primary_key: tuple[str, ...]
    omit_fields: set[str]
    _id_type: type[_ID]
    _foreign_rows: set[tuple[str, ...]]

    def __init__(self, record_type: Optional[dict[str, TypeAlias]] = None) -> None:
        for k, c in (*self.fields.items(), *self.inputs.items()):
            c["props"].setdefault("key", k)

        # For runtime type checking only.
        if record_type is None:
            record_type = {k.removeprefix("data."): Any for k in self.inputs}
        self._raw_record_type = record_type
        self._record_type = TypedDict("RecordType", record_type, total=False)  # type: ignore[misc]

    @final
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
    async def get_one(self, record_id: _ID, meta: Meta) -> Record:
        """Return the matching record."""

    @abstractmethod
    async def get_many(self, record_ids: Sequence[_ID], meta: Meta) -> list[Record]:
        """Return the matching records."""

    @abstractmethod
    async def get_many_ref(self, params: GetManyRefParams) -> tuple[list[Record], int]:
        """Return list of records and total count available (when not paginating)."""

    @abstractmethod
    async def update(self, record_id: _ID, data: Record, previous_data: Record,
                     meta: Meta) -> Record:
        """Update the record and return the updated record."""

    @abstractmethod
    async def update_many(self, record_ids: Sequence[_ID], data: Record, meta: Meta) -> list[_ID]:
        """Update multiple records and return the IDs of updated records."""

    @abstractmethod
    async def create(self, data: Record, meta: Meta) -> Record:
        """Create a new record and return the created record."""

    @abstractmethod
    async def delete(self, record_id: _ID, previous_data: Record, meta: Meta) -> Record:
        """Delete a record and return the deleted record."""

    @abstractmethod
    async def delete_many(self, record_ids: Sequence[_ID], meta: Meta) -> list[_ID]:
        """Delete the matching records and return their IDs."""

    async def get_many_ref_name(self, target: str, meta: Meta) -> str:
        """Return the resource name for the reference.

        This can be used to change which resource should be returned by get_many_ref().

        For example, if we have an SQLAlchemy model called 'parent' with a relationship
        called children, then a normal get_many_ref_name() call would go to the 'child'
        model with the details from the parent, and the default behaviour would work.

        However, the SQLAlchemy backend uses the meta to switch this and send the request
        to the 'parent' model instead and then use the children ORM attribute to fetch
        the referenced resources, thus requiring this method to return 'child'.
        This allows the SQLAlchemy backend to support complex relationships (e.g.
        many-to-many) without needing react-admin to know the details.
        """
        return self.name

    # https://marmelab.com/react-admin/DataProviderWriting.html

    @final
    async def _get_list(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.view", context=(request, None))
        query = check(GetListParams, request.query)
        self._process_list_query(query, request)

        raw_results, total = await self.get_list(query)
        results = [await self._convert_record(r, request) for r in raw_results
                   if await permits(request, f"admin.{self.name}.view", context=(request, r))]
        return json_response({"data": results, "total": total})

    @final
    async def _get_one(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.view", context=(request, None))
        query = check(GetOneParams, request.query)
        record_id = check(self._id_type, query["id"].split("|"))

        result = await self.get_one(record_id, query.get("meta"))
        if not await permits(request, f"admin.{self.name}.view", context=(request, result)):
            raise web.HTTPForbidden()
        return json_response({"data": await self._convert_record(result, request)})

    @final
    async def _get_many(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.view", context=(request, None))
        query = check(GetManyParams, request.query)
        record_ids = check(tuple[self._id_type, ...], (q.split("|") for q in query["ids"]))  # type: ignore[name-defined]

        raw_results = await self.get_many(record_ids, query.get("meta"))
        if not raw_results:
            raise web.HTTPNotFound()

        results = [await self._convert_record(r, request) for r in raw_results
                   if await permits(request, f"admin.{self.name}.view", context=(request, r))]
        return json_response({"data": results})

    @final
    async def _get_many_ref(self, request: web.Request) -> web.Response:
        query = check(GetManyRefAPIParams, request.query)
        meta = query["filter"].pop("__meta__", None)
        if meta is not None:
            query["meta"] = check(dict[str, object], meta)
        reference = await self.get_many_ref_name(query["target"], query.get("meta"))
        ref_model = request.app[resources_key][reference]

        await check_permission(request, f"admin.{ref_model.name}.view", context=(request, None))

        ref_model._process_list_query(query, request)

        if query["target"].startswith("fk_"):
            target = tuple(query["target"].removeprefix("fk_").split("__"))
            record_id = tuple(check(ref_model._raw_record_type[k], v) for k, v in zip(query["target"], query["id"].split("|")))
        else:
            target = (query["target"],)
            record_id = check(ref_model._id_type, query["id"].split("|"))

        raw_results, total = await self.get_many_ref({**query, "target": target, "id": record_id})

        results = [await ref_model._convert_record(r, request) for r in raw_results
                   if await permits(request, f"admin.{ref_model.name}.view", context=(request, r))]
        return json_response({"data": results, "total": total})

    @final
    async def _create(self, request: web.Request) -> web.Response:
        query = check(CreateParams, request.query)
        # TODO(Pydantic): Dissallow extra arguments
        for k in query["data"]["data"]:
            if k not in self.inputs:
                raise web.HTTPBadRequest(reason=f"Invalid field '{k}'")
        record = self._check_record(query["data"]["data"])
        await check_permission(request, f"admin.{self.name}.add", context=(request, record))
        for k, v in record.items():
            if v is not None:
                await check_permission(request, f"admin.{self.name}.{k}.add",
                                       context=(request, record))

        result = await self.create(record, query.get("meta"))
        return json_response({"data": await self._convert_record(result, request)})

    @final
    async def _update(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.edit", context=(request, None))
        query = check(UpdateParams, request.query)
        record_id = check(self._id_type, query["id"].split("|"))
        # TODO(Pydantic): Dissallow extra arguments
        for k in query["data"]["data"]:
            if k not in self.inputs:
                raise web.HTTPBadRequest(reason=f"Invalid field '{k}'")
        record = self._check_record(query["data"]["data"])
        previous_data = self._check_record(query["previousData"]["data"])

        # Check original record is allowed by permission filters.
        original = await self.get_one(record_id, query.get("meta"))
        if not await permits(request, f"admin.{self.name}.edit", context=(request, original)):
            raise web.HTTPForbidden()

        # Filter rather than forbid because react-admin still sends fields without an
        # input component. The query may not be the complete dict though, so we must
        # pass original for testing.
        record = await self.filter_by_permissions(request, "edit", record, original)
        # Check new values are allowed by permission filters.
        if not await permits(request, f"admin.{self.name}.edit", context=(request, record)):
            raise web.HTTPForbidden()

        if not record:
            raise web.HTTPBadRequest(reason="No allowed fields to change.")

        result = await self.update(record_id, record, previous_data, query.get("meta"))
        return json_response({"data": await self._convert_record(result, request)})

    @final
    async def _update_many(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.edit", context=(request, None))
        query = check(UpdateManyParams, request.query)
        record_ids = check(tuple[self._id_type, ...], (i.split("|") for i in query["ids"]))  # type: ignore[name-defined]
        # TODO(Pydantic): Dissallow extra arguments
        for k in query["data"]:
            if k not in self.inputs:
                raise web.HTTPBadRequest(reason=f"Invalid field '{k}'")
        record = self._check_record(query["data"])

        # Check original records are allowed by permission filters.
        originals = await self.get_many(record_ids, query.get("meta"))
        if not originals:
            raise web.HTTPNotFound()
        allowed = (permits(request, f"admin.{self.name}.edit", context=(request, r))
                   for r in originals)
        allowed_f = (permits(request, f"admin.{self.name}.{k}.edit", context=(request, r))
                     for r in originals for k in record)
        if not all(await asyncio.gather(*allowed, *allowed_f)):
            raise web.HTTPForbidden()
        # Check new values are allowed by permission filters.
        if not await permits(request, f"admin.{self.name}.edit", context=(request, record)):
            raise web.HTTPForbidden()

        ids = await self.update_many(record_ids, record, query.get("meta"))
        # get_many() is called above, so we can be sure there will be results here.
        return json_response({"data": self._convert_ids(ids)})

    @final
    async def _delete(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.delete", context=(request, None))
        query = check(DeleteParams, request.query)
        record_id = check(self._id_type, query["id"].split("|"))
        previous_data = self._check_record(query["previousData"]["data"])

        original = await self.get_one(record_id, query.get("meta"))
        if not await permits(request, f"admin.{self.name}.delete", context=(request, original)):
            raise web.HTTPForbidden()

        result = await self.delete(record_id, previous_data, query.get("meta"))
        return json_response({"data": await self._convert_record(result, request)})

    @final
    async def _delete_many(self, request: web.Request) -> web.Response:
        await check_permission(request, f"admin.{self.name}.delete", context=(request, None))
        query = check(DeleteManyParams, request.query)
        record_ids = check(tuple[self._id_type, ...], (i.split("|") for i in query["ids"]))  # type: ignore[name-defined]

        originals = await self.get_many(record_ids, query.get("meta"))
        allowed = await asyncio.gather(*(permits(request, f"admin.{self.name}.delete",
                                                 context=(request, r)) for r in originals))
        if not all(allowed):
            raise web.HTTPForbidden()

        ids = await self.delete_many(record_ids, query.get("meta"))
        if not ids:
            raise web.HTTPNotFound()
        return json_response({"data": self._convert_ids(ids)})

    @final
    def _check_record(self, record: Record) -> Record:
        """Check and convert input record."""
        return check(self._record_type, record)

    @final
    async def _convert_record(self, record: Record, request: web.Request) -> APIRecord:
        """Convert record to correct output format."""
        record = await self.filter_by_permissions(request, "view", record)

        foreign_keys = {fk(*keys): None if any(record[k] is None for k in keys)
                        else "|".join(str(record[k]) for k in keys)
                        for keys in self._foreign_rows if all(k in record for k in keys)}
        return {
            "id": "|".join(str(record[pk]) for pk in self.primary_key),
            "data": record,
            **foreign_keys  # type: ignore[typeddict-item]
        }

    @final
    def _convert_ids(self, ids: Sequence[_ID]) -> tuple[str, ...]:
        """Convert IDs to correct output format."""
        return tuple(str(i) for i in ids)

    def _process_list_query(self, query: _ListQuery, request: web.Request) -> None:
        # When sort order refers to "id", this should be translated to primary key.
        if query["sort"]["field"] == "id":
            query["sort"]["field"] = self.primary_key[0]
        else:
            query["sort"]["field"] = query["sort"]["field"].removeprefix("data.")

        query["filter"].update(check(dict[str, object], query["filter"].pop("data", {})))

        merged_filter = {}
        for k, v in query["filter"].items():
            if k.startswith("fk_"):
                v = check(str, v)
                for c, cv in zip(k.removeprefix("fk_").split("__"), v.split("|")):
                    merged_filter[c] = check(self._raw_record_type[c], cv)
            else:
                merged_filter[k] = check(self._raw_record_type[k], v)
        query["filter"] = merged_filter

        # Add filters from advanced permissions.
        # The permissions will be cached on the request from a previous permissions check.
        permissions = permissions_as_dict(request["aiohttpadmin_permissions"])
        filters = permissions.get(f"admin.{self.name}.view",
                                  permissions.get(f"admin.{self.name}.*", {}))
        for k, v in filters.items():
            query["filter"][k] = v

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
            web.get(url + "/ref", self._get_many_ref, name=self.name + "_get_many_ref"),
            web.post(url, self._create, name=self.name + "_create"),
            web.put(url + "/update", self._update, name=self.name + "_update"),
            web.put(url + "/update_many", self._update_many, name=self.name + "_update_many"),
            web.delete(url + "/one", self._delete, name=self.name + "_delete"),
            web.delete(url, self._delete_many, name=self.name + "_delete_many")
        )
