from unittest.mock import AsyncMock, create_autospec

import pytest
from aiohttp import web
from aiohttp_security import AbstractAuthorizationPolicy
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

import aiohttp_admin
from aiohttp_admin.backends.sqlalchemy import SAResource
from _auth import DummyAuthPolicy, check_credentials, identity_callback

@pytest.fixture
def base() -> DeclarativeBase:
    class Base(DeclarativeBase):
        """Base model."""


    return Base

@pytest.fixture
def mock_engine() -> AsyncMock:
    return create_autospec(AsyncEngine, instance=True, spec_set=True)

@pytest.fixture
def create_admin_client(base: DeclarativeBase, aiohttp_client):
    async def admin_client(auth_policy: AbstractAuthorizationPolicy):
        class DummyModel(base):
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

        schema = {
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
async def admin_client(create_admin_client):
    return await create_admin_client(DummyAuthPolicy())

@pytest.fixture
def login():
    async def do_login(admin_client):
        url = admin_client.app["admin"].router["token"].url_for()
        login = {"username": "admin", "password": "admin123"}
        async with admin_client.post(url, json=login) as resp:
            assert resp.status == 200
            token = resp.headers["X-Token"]

        return {"Authorization": token}

    return do_login
