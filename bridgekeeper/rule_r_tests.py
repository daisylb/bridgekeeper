import pytest
from shrubberies.factories import ShrubberyFactory, StoreFactory, UserFactory
from shrubberies.models import Shrubbery, Store

from .rules import R

pytestmark = pytest.mark.django_db


def test_constant_attribute():
    user = UserFactory()
    s1 = StoreFactory(name="a")
    s2 = StoreFactory(name="b")
    pr = R(name="a")

    assert pr.check(user, s1)
    assert not pr.check(user, s2)

    filtered_qs_r = pr.filter(user, Store.objects.all())
    assert filtered_qs_r.count() == 1
    assert s1 in filtered_qs_r
    assert s2 not in filtered_qs_r


def test_user_func_attribute():
    u1 = UserFactory(username="a")
    u2 = UserFactory(username="b")
    s1 = StoreFactory(name="a")
    s2 = StoreFactory(name="b")
    pr = R(name=lambda u: u.username)

    assert pr.check(u1, s1)
    assert pr.check(u2, s2)
    assert not pr.check(u1, s2)
    assert not pr.check(u2, s1)

    qs1_r = pr.filter(u1, Store.objects.all())
    qs2_r = pr.filter(u2, Store.objects.all())
    assert qs1_r.count() == 1
    assert s1 in qs1_r
    assert s2 not in qs1_r
    assert qs2_r.count() == 1
    assert s2 in qs2_r
    assert s1 not in qs2_r


def test_when_called_without_object():
    user = UserFactory(username="a")
    pr = R(name=lambda u: u.username)
    assert not pr.check(user)


def test_relation_to_user():
    u1 = UserFactory()
    u2 = UserFactory()
    s1 = ShrubberyFactory(branch=u1.profile.branch)
    s2 = ShrubberyFactory(branch=u2.profile.branch)
    belongs_to_branch_r = R(branch=lambda u: u.profile.branch)

    assert belongs_to_branch_r.check(u1, s1)
    assert belongs_to_branch_r.check(u2, s2)
    assert not belongs_to_branch_r.check(u1, s2)
    assert not belongs_to_branch_r.check(u2, s1)

    qs1_r = belongs_to_branch_r.filter(u1, Shrubbery.objects.all())
    qs2_r = belongs_to_branch_r.filter(u2, Shrubbery.objects.all())
    assert qs1_r.count() == 1
    assert s1 in qs1_r
    assert s2 not in qs1_r
    assert qs2_r.count() == 1
    assert s2 in qs2_r
    assert s1 not in qs2_r


def test_relation_never_global():
    user = UserFactory()
    belongs_to_branch_r = R(branch=lambda u: u.profile.branch)
    assert not belongs_to_branch_r.check(user)


def test_traverse_fk_user_func():
    user = UserFactory()
    shrubbery_match = ShrubberyFactory(branch__store=user.profile.branch.store)
    shrubbery_nomatch = ShrubberyFactory()
    store_check_r = R(branch__store=lambda user: user.profile.branch.store)

    assert store_check_r.check(user, shrubbery_match)
    assert not store_check_r.check(user, shrubbery_nomatch)

    qs = store_check_r.filter(user, Shrubbery.objects.all())
    assert shrubbery_match in qs
    assert shrubbery_nomatch not in qs


def test_nested_rule_object():
    user = UserFactory()
    shrubbery_match = ShrubberyFactory(branch__store=user.profile.branch.store)
    shrubbery_nomatch = ShrubberyFactory()
    store_check_r = R(branch=R(store=lambda user: user.profile.branch.store))

    assert store_check_r.check(user, shrubbery_match)
    assert not store_check_r.check(user, shrubbery_nomatch)

    qs = store_check_r.filter(user, Shrubbery.objects.all())
    assert shrubbery_match in qs
    assert shrubbery_nomatch not in qs


def test_many_relation_to_user():
    s1 = StoreFactory()
    s2 = StoreFactory()
    u1 = UserFactory(profile__branch__store=s1)
    u2 = UserFactory(profile__branch__store=s2)
    user_branch_in_store = R(branch=lambda u: u.profile.branch)

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
