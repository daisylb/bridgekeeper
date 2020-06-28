import pytest
from shrubberies.factories import ShrubberyFactory, UserFactory
from shrubberies.models import Shrubbery

from .rules import Is, Relation


@pytest.mark.django_db
def test_relation_to_user():
    u1 = UserFactory()
    u2 = UserFactory()
    s1 = ShrubberyFactory(branch=u1.profile.branch)
    s2 = ShrubberyFactory(branch=u2.profile.branch)
    belongs_to_branch = Relation("branch", Is(lambda u: u.profile.branch))

    assert belongs_to_branch.check(u1, s1)
    assert belongs_to_branch.check(u2, s2)
    assert not belongs_to_branch.check(u1, s2)
    assert not belongs_to_branch.check(u2, s1)

    qs1 = belongs_to_branch.filter(u1, Shrubbery.objects.all())
    qs2 = belongs_to_branch.filter(u2, Shrubbery.objects.all())
    assert qs1.count() == 1
    assert s1 in qs1
    assert s2 not in qs1
    assert qs2.count() == 1
    assert s2 in qs2
    assert s1 not in qs2


@pytest.mark.django_db
def test_relation_never_global():
    user = UserFactory()
    belongs_to_branch = Relation("branch", Is(lambda u: u.profile.branch))
    assert not belongs_to_branch.check(user)
