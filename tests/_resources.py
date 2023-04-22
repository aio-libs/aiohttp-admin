from typing import Union

from aiohttp_admin.backends.abc import (
    AbstractAdminResource, CreateParams, DeleteManyParams, DeleteParams, GetListParams,
    GetManyParams, GetOneParams, UpdateManyParams, UpdateParams, Record)
from aiohttp_admin.types import FieldState, InputState


class DummyResource(AbstractAdminResource):
    def __init__(self, name: str, fields: dict[str, FieldState],
                 inputs: dict[str, InputState], primary_key: str):
        self.name = name
        self.fields = fields
        self.inputs = inputs
        self.primary_key = primary_key
        super().__init__()

    async def get_list(self, params: GetListParams) -> tuple[list[Record], int]:
        return ([], 0)

    async def get_one(self, params: GetOneParams) -> Record:
        return {}

    async def get_many(self, params: GetManyParams) -> list[Record]:
        return []

    async def update(self, params: UpdateParams) -> Record:
        return {}

    async def update_many(self, params: UpdateManyParams) -> list[Union[int, str]]:
        return []

    async def create(self, params: CreateParams) -> Record:
        return {}

    async def delete(self, params: DeleteParams) -> Record:
        return {}

    async def delete_many(self, params: DeleteManyParams) -> list[Union[int, str]]:
        return []
