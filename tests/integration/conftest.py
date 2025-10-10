from pathlib import Path
from typing import Any

import pytest


def pytest_addoption(parser: Any) -> None:
    """Configurable default for device serial # when running hardware tests"""
    parser.addoption("--endpoint", action="store", default="")
    parser.addoption("--device_id", action="store", default="00000")
    parser.addoption("--alias", action="store", default="test_role")


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent.parent.parent.resolve()


@pytest.fixture()
def endpoint(pytestconfig: Any) -> str:
    return pytestconfig.getoption("endpoint")


@pytest.fixture()
def alias(pytestconfig: Any) -> str:
    return pytestconfig.getoption("alias")


@pytest.fixture()
def device_id(pytestconfig: Any) -> str:
    return pytestconfig.getoption("device_id")


@pytest.fixture()
def cert_file(fixture_dir: Path, device_id: str) -> Path:
    return fixture_dir / f"{device_id}-certificate.pem.crt"


@pytest.fixture()
def key_file(fixture_dir: Path, device_id: str) -> Path:
    return fixture_dir / f"{device_id}-private.pem.key"


@pytest.fixture()
def cert_root(fixture_dir: Path, device_id: str) -> Path:
    return fixture_dir / "CARoot.pem"
