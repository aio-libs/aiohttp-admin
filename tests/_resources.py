from typing import Sequence

from aiohttp_admin.backends.abc import (AbstractAdminResource, GetListParams,
                                        GetManyRefParams, Meta, Record)
from aiohttp_admin.types import ComponentState, InputState


class DummyResource(AbstractAdminResource[tuple[str]]):
    def __init__(self, name: str, fields: dict[str, ComponentState],
                 inputs: dict[str, InputState], primary_key: str):
        self.name = name
        self.fields = fields
        self.inputs = inputs
        self.primary_key = (primary_key,)
        self.omit_fields = set()
        self._id_type = tuple[str]  # type: ignore[assignment]
        self._foreign_rows = set()
        super().__init__()

    async def get_list(self, params: GetListParams) -> tuple[list[Record], int]:  # pragma: no cover
        raise NotImplementedError()

    async def get_one(self, record_id: tuple[str], meta: Meta) -> Record:  # pragma: no cover
        raise NotImplementedError()

    async def get_many(self, record_ids: Sequence[tuple[str]], meta: Meta) -> list[Record]:  # pragma: no cover
        raise NotImplementedError()

    async def get_many_ref(self, params: GetManyRefParams) -> tuple[list[Record], int]:  # pragma: no cover
        raise NotImplementedError()

    async def update(self, record_id: tuple[str], data: Record, previous_data: Record, meta: Meta) -> Record:  # pragma: no cover
        raise NotImplementedError()

    async def update_many(self, record_ids: Sequence[tuple[str]], data: Record, meta: Meta) -> list[tuple[str]]:  # pragma: no cover
        raise NotImplementedError()

    async def create(self, data: Record, meta: Meta) -> Record:  # pragma: no cover
        raise NotImplementedError()

    async def delete(self, record_id: tuple[str], previous_data: Record, meta: Meta) -> Record:  # pragma: no cover
        raise NotImplementedError()

    async def delete_many(self, record_ids: Sequence[tuple[str]], meta: Meta) -> list[tuple[str]]:  # pragma: no cover
        raise NotImplementedError()
