from typing import Union

from aiohttp_admin.backends.abc import (
    AbstractAdminResource, CreateParams, DeleteManyParams, DeleteParams, GetListParams,
    GetManyParams, GetOneParams, Record, UpdateManyParams, UpdateParams)
from aiohttp_admin.types import FieldState, InputState


class DummyResource(AbstractAdminResource):
    def __init__(self, name: str, fields: dict[str, FieldState],
                 inputs: dict[str, InputState], primary_key: str):
        self.name = name
        self.fields = fields
        self.inputs = inputs
        self.primary_key = primary_key
        self.omit_fields = set()
        super().__init__()

    async def get_list(self, params: GetListParams) -> tuple[list[Record], int]:  # pragma: no cover  # noqa: B950
        raise NotImplementedError()

    async def get_one(self, params: GetOneParams) -> Record:  # pragma: no cover
        raise NotImplementedError()

    async def get_many(self, params: GetManyParams) -> list[Record]:  # pragma: no cover
        raise NotImplementedError()

    async def update(self, params: UpdateParams) -> Record:  # pragma: no cover
        raise NotImplementedError()

    async def update_many(self, params: UpdateManyParams) -> list[Union[int, str]]:  # pragma: no cover  # noqa: B950
        raise NotImplementedError()

    async def create(self, params: CreateParams) -> Record:  # pragma: no cover
        raise NotImplementedError()

    async def delete(self, params: DeleteParams) -> Record:  # pragma: no cover
        raise NotImplementedError()

    async def delete_many(self, params: DeleteManyParams) -> list[Union[int, str]]:  # pragma: no cover  # noqa: B950
        raise NotImplementedError()
