import pytest
from shrubberies import factories

from . import backends, permission_map
from . import perms as global_permission_map
from . import rules


@pytest.fixture
def perms():
    return permission_map.PermissionMap()


@pytest.fixture
def backend(perms):
    return backends.RulePermissionBackend(permission_map=perms)


@rules.blanket_rule
def username_starts_with_a(user):
    return user.username.startswith("a")


store_name_matches_username = rules.Attribute("name", lambda u: u.username)


@pytest.mark.django_db
def test_blanket_rule(perms, backend):
    user_a = factories.UserFactory(username="aaa")
    user_b = factories.UserFactory(username="bbb")
    perms["foo.username_starts_with_a"] = username_starts_with_a
    assert backend.has_perm(user_a, "foo.username_starts_with_a")
    assert not backend.has_perm(user_b, "foo.username_starts_with_a")
    assert backend.has_module_perms(user_a, "foo")
    assert not backend.has_module_perms(user_b, "foo")


@pytest.mark.django_db
def test_queryset_rule(perms, backend):
    user_a = factories.UserFactory(username="aaa")
    user_b = factories.UserFactory(username="bbb")
    perms["foo.bar"] = store_name_matches_username
    store_a = factories.StoreFactory(name="aaa")
    store_b = factories.StoreFactory(name="bbb")
    assert backend.has_perm(user_a, "foo.bar", store_a)
    assert backend.has_perm(user_b, "foo.bar", store_b)
    assert not backend.has_perm(user_a, "foo.bar", store_b)
    assert not backend.has_perm(user_b, "foo.bar", store_a)
    assert backend.has_module_perms(user_a, "foo")
    assert backend.has_module_perms(user_b, "foo")
    assert not backend.has_perm(user_a, "foo.bar")
    assert not backend.has_perm(user_b, "foo.bar")


@pytest.mark.django_db
def test_module_perms_with_no_matching_objects(perms, backend):
    user_b = factories.UserFactory(username="bbb")
    perms["foo.bar"] = store_name_matches_username
    factories.StoreFactory(name="aaa")
    assert backend.has_module_perms(user_b, "foo")


@pytest.mark.django_db
def test_backend_uses_global_permission_map():
    assert isinstance(global_permission_map, permission_map.PermissionMap)
    backend = backends.RulePermissionBackend()
    assert backend.permission_map is global_permission_map
