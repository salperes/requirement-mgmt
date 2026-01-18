import os
import tempfile
import warnings
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

warnings.filterwarnings("ignore", category=DeprecationWarning, module="passlib\\.utils")

# Ensure settings pick up test DB before any imports use settings.
db_path = os.path.join(tempfile.gettempdir(), "rms_test.db")
os.environ["RMS_DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
os.environ["RMS_JWT_SECRET"] = "test-secret"

from src.shared.settings import settings
from src.db import session as db_session
from src.api import deps as api_deps

settings.database_url = os.environ["RMS_DATABASE_URL"]

test_engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

db_session.engine = test_engine
db_session.SessionLocal = SessionLocal
api_deps.SessionLocal = SessionLocal


@pytest.fixture(scope="session", autouse=True)
def set_test_env() -> None:
    return None


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    from src.app.main import app
    from src.db.base import Base

    Base.metadata.create_all(bind=db_session.engine)

    with TestClient(app) as test_client:
        yield test_client
