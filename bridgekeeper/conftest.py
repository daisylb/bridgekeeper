import bridgekeeper
import pytest


@pytest.yield_fixture(autouse=True)
def clean_global_permissions_map():
    for k in list(bridgekeeper.perms.keys()):
        del bridgekeeper.perms[k]
    yield
