import pytest
from shrubberies.factories import StoreFactory, UserFactory
from shrubberies.models import Store

from .rules import Attribute


@pytest.mark.django_db
def test_constant_attribute():
    user = UserFactory()
    s1 = StoreFactory(name="a")
    s2 = StoreFactory(name="b")
    p = Attribute("name", "a")

    assert p.check(user, s1)
    assert not p.check(user, s2)

    filtered_qs = p.filter(user, Store.objects.all())
    assert filtered_qs.count() == 1
    assert s1 in filtered_qs
    assert s2 not in filtered_qs


@pytest.mark.django_db
def test_user_func_attribute():
    u1 = UserFactory(username="a")
    u2 = UserFactory(username="b")
    s1 = StoreFactory(name="a")
    s2 = StoreFactory(name="b")
    p = Attribute("name", lambda u: u.username)

    assert p.check(u1, s1)
    assert p.check(u2, s2)
    assert not p.check(u1, s2)
    assert not p.check(u2, s1)

    qs1 = p.filter(u1, Store.objects.all())
    qs2 = p.filter(u2, Store.objects.all())
    assert qs1.count() == 1
    assert s1 in qs1
    assert s2 not in qs1
    assert qs2.count() == 1
    assert s2 in qs2
    assert s1 not in qs2


@pytest.mark.django_db
def test_when_called_without_object():
    user = UserFactory(username="a")
    p = Attribute("name", lambda u: u.username)
    assert not p.check(user)


@pytest.mark.django_db
def test_inversion_of_attribute():
    u1 = UserFactory(username="a")
    u2 = UserFactory(username="b")
    s1 = StoreFactory(name="a")
    s2 = StoreFactory(name="b")
    p = ~Attribute("name", lambda u: u.username)

    assert p.check(u1, s2)
    assert p.check(u2, s1)
