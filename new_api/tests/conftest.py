import pytest

from new_api.containers import Container


@pytest.fixture(scope="session")
def containers():
    return Container()
