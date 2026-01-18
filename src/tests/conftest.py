import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def set_test_env() -> None:
    db_path = os.path.join(tempfile.gettempdir(), "rms_test.db")
    os.environ["RMS_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
    os.environ["RMS_JWT_SECRET"] = "test-secret"


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    from src.app.main import app
    from src.db.base import Base
    from src.db.session import engine

    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client