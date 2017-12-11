import pytest

from . import perms
from .permission_map import PermissionMap


@pytest.yield_fixture(autouse=True)
def clean_global_permissions_map():
    yield
    perms = PermissionMap()
