import pytest

from .. import registry as registry_mod
from .. import predicates
from ....apps.accounts.factories import UserFactory
from ....apps.applicants import factories as appl_factories


@pytest.fixture
def registry():
    return registry_mod.Registry()


@pytest.fixture
def backend(registry):
    return registry_mod.RulePermissionBackend(registry=registry)


@predicates.ambient
def username_starts_with_a(user):
    return user.username.startswith('a')


applicant_first_name_matches_username = predicates.Attribute(
    'first_name', lambda u: u.username)


@pytest.mark.django_db
def test_ambient_predicate(registry, backend):
    user_a = UserFactory(username='aaa')
    user_b = UserFactory(username='bbb')
    registry['foo.username_starts_with_a'] = username_starts_with_a
    assert backend.has_perm(user_a, 'foo.username_starts_with_a')
    assert not backend.has_perm(user_b, 'foo.username_starts_with_a')
    assert backend.has_module_perms(user_a, 'foo')
    assert not backend.has_module_perms(user_b, 'foo')


@pytest.mark.django_db
def test_queryset_predicate(registry, backend):
    user_a = UserFactory(username='aaa')
    user_b = UserFactory(username='bbb')
    registry['foo.bar'] = applicant_first_name_matches_username
    applicant_a = appl_factories.ApplicantFactory(first_name='aaa')
    applicant_b = appl_factories.ApplicantFactory(first_name='bbb')
    assert backend.has_perm(user_a, 'foo.bar', applicant_a)
    assert backend.has_perm(user_b, 'foo.bar', applicant_b)
    assert not backend.has_perm(user_a, 'foo.bar', applicant_b)
    assert not backend.has_perm(user_b, 'foo.bar', applicant_a)
    assert backend.has_module_perms(user_a, 'foo')
    assert backend.has_module_perms(user_b, 'foo')
    assert not backend.has_perm(user_a, 'foo.bar')
    assert not backend.has_perm(user_b, 'foo.bar')


@pytest.mark.django_db
def test_module_perms_with_no_matching_objects(registry, backend):
    user_b = UserFactory(username='bbb')
    registry['foo.bar'] = applicant_first_name_matches_username
    appl_factories.ApplicantFactory(first_name='aaa')
    assert backend.has_module_perms(user_b, 'foo')
