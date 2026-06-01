import logging
import warnings

import pytest
from fastapi.testclient import TestClient

from app.core.app import create_app
from app.db.session import get_db_session


warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("rag_resover").setLevel(logging.WARNING)


async def override_db_session():
    yield object()


@pytest.fixture
def app():
    application = create_app()
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_with_fake_db(app):
    app.dependency_overrides[get_db_session] = override_db_session
    with TestClient(app) as test_client:
        yield test_client
