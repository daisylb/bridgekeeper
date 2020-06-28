import pytest
from shrubberies.factories import StoreFactory, UserFactory
from shrubberies.models import Store

from .rules import Is, ManyRelation


@pytest.mark.django_db
def test_many_relation_to_user():
    s1 = StoreFactory()
    s2 = StoreFactory()
    u1 = UserFactory(profile__branch__store=s1)
    u2 = UserFactory(profile__branch__store=s2)
    user_branch_in_store = ManyRelation("branch", Is(lambda u: u.profile.branch))

    assert user_branch_in_store.check(u1, s1)
    assert user_branch_in_store.check(u2, s2)
    assert not user_branch_in_store.check(u1, s2)
    assert not user_branch_in_store.check(u2, s1)

    qs1 = user_branch_in_store.filter(u1, Store.objects.all())
    qs2 = user_branch_in_store.filter(u2, Store.objects.all())
    assert qs1.count() == 1
    assert s1 in qs1
    assert s2 not in qs1
    assert qs2.count() == 1
    assert s2 in qs2
    assert s1 not in qs2


@pytest.mark.django_db
def test_many_relation_never_global():
    user = UserFactory()
    user_branch_in_store = ManyRelation("branch", Is(lambda u: u.profile.branch))
    assert not user_branch_in_store.check(user)
