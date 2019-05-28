import pytest
from shrubberies.factories import StoreFactory, UserFactory
from shrubberies.models import Store

from .rules import Attribute, R


@pytest.mark.django_db
def test_constant_attribute():
    user = UserFactory()
    s1 = StoreFactory(name='a')
    s2 = StoreFactory(name='b')
    p = Attribute('name', 'a')
    pr = R(name='a')

    assert p.check(user, s1)
    assert pr.check(user, s1)
    assert not p.check(user, s2)
    assert not pr.check(user, s2)

    filtered_qs = p.filter(user, Store.objects.all())
    filtered_qs_r = pr.filter(user, Store.objects.all())
    assert filtered_qs.count() == 1
    assert filtered_qs_r.count() == 1
    assert s1 in filtered_qs
    assert s1 in filtered_qs_r
    assert s2 not in filtered_qs
    assert s2 not in filtered_qs_r


@pytest.mark.django_db
def test_user_func_attribute():
    u1 = UserFactory(username='a')
    u2 = UserFactory(username='b')
    s1 = StoreFactory(name='a')
    s2 = StoreFactory(name='b')
    p = Attribute('name', lambda u: u.username)
    pr = R(name=lambda u: u.username)

    assert p.check(u1, s1)
    assert pr.check(u1, s1)
    assert p.check(u2, s2)
    assert pr.check(u2, s2)
    assert not p.check(u1, s2)
    assert not pr.check(u1, s2)
    assert not p.check(u2, s1)
    assert not pr.check(u2, s1)

    qs1 = p.filter(u1, Store.objects.all())
    qs2 = p.filter(u2, Store.objects.all())
    qs1_r = pr.filter(u1, Store.objects.all())
    qs2_r = pr.filter(u2, Store.objects.all())
    assert qs1.count() == 1
    assert qs1_r.count() == 1
    assert s1 in qs1
    assert s1 in qs1_r
    assert s2 not in qs1
    assert s2 not in qs1_r
    assert qs2.count() == 1
    assert qs2_r.count() == 1
    assert s2 in qs2
    assert s2 in qs2_r
    assert s1 not in qs2
    assert s1 not in qs2_r


@pytest.mark.django_db
def test_when_called_without_object():
    user = UserFactory(username='a')
    p = Attribute('name', lambda u: u.username)
    pr = R(name=lambda u: u.username)
    assert not p.check(user)
    assert not pr.check(user)
