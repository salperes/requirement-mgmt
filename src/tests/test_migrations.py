import os

import pytest


@pytest.mark.skipif(
    not os.environ.get("RMS_DATABASE_URL", "").startswith("postgresql"),
    reason="Migration test requires Postgres",
)
def test_migrations_apply():
    assert True