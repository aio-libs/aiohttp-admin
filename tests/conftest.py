from typing import Awaitable, Callable, Type
from unittest.mock import AsyncMock, create_autospec

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from aiohttp_security import AbstractAuthorizationPolicy
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

import aiohttp_admin
from _auth import DummyAuthPolicy, check_credentials, identity_callback
from aiohttp_admin.backends.sqlalchemy import SAResource

_CreateAdmin = Callable[[AbstractAuthorizationPolicy], Awaitable[TestClient]]


@pytest.fixture
def base() -> Type[DeclarativeBase]:
    class Base(DeclarativeBase):
        """Base model."""

    return Base


@pytest.fixture
def mock_engine() -> AsyncMock:
    return create_autospec(AsyncEngine, instance=True, spec_set=True)  # type: ignore[no-any-return] # noqa: B950


@pytest.fixture
def create_admin_client(  # type: ignore[misc,no-any-unimported]
    base: DeclarativeBase, aiohttp_client: Callable[[web.Application], Awaitable[TestClient]]
) -> Callable[[AbstractAuthorizationPolicy], Awaitable[TestClient]]:
    async def admin_client(auth_policy: AbstractAuthorizationPolicy) -> TestClient:  # type: ignore[no-any-unimported] # noqa: B950
        class DummyModel(base):  # type: ignore[misc,valid-type]
            __tablename__ = "dummy"

            id: Mapped[int] = mapped_column(primary_key=True)

        app = web.Application()
        app["model"] = DummyModel
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        app["db"] = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)
        async with app["db"].begin() as sess:
            sess.add(DummyModel())

        schema: aiohttp_admin.Schema = {
            "security": {
                "check_credentials": check_credentials,
                "identity_callback": identity_callback,
                "secure": False
            },
            "resources": (
                {"model": SAResource(engine, DummyModel)},
            )
        }
        app["admin"] = aiohttp_admin.setup(app, schema, auth_policy)

        return await aiohttp_client(app)

    return admin_client


@pytest.fixture
async def admin_client(create_admin_client: _CreateAdmin) -> TestClient:  # type: ignore[misc,no-any-unimported] # noqa: B950
    return await create_admin_client(DummyAuthPolicy())


@pytest.fixture
def login() -> Callable[[TestClient], Awaitable[dict[str, str]]]:
    async def do_login(admin_client: TestClient) -> dict[str, str]:
        assert admin_client.app
        url = admin_client.app["admin"].router["token"].url_for()
        login = {"username": "admin", "password": "admin123"}
        async with admin_client.post(url, json=login) as resp:
            assert resp.status == 200
            token = resp.headers["X-Token"]

        return {"Authorization": token}

    return do_login
