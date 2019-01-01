import pytest
from django.contrib.auth.models import User
from shrubberies.factories import UserFactory
from shrubberies.models import Profile

from .rules import Is, current_user


@pytest.mark.django_db
def test_is_user_function():
    u1 = UserFactory()
    u2 = UserFactory()
    is_own_profile = Is(lambda u: u.profile)

    assert is_own_profile.check(u1, u1.profile)
    assert is_own_profile.check(u2, u2.profile)
    assert not is_own_profile.check(u1, u2.profile)
    assert not is_own_profile.check(u2, u1.profile)

    qs1 = is_own_profile.filter(u1, Profile.objects.all())
    qs2 = is_own_profile.filter(u2, Profile.objects.all())
    assert qs1.count() == 1
    assert u1.profile in qs1
    assert u2.profile not in qs1
    assert qs2.count() == 1
    assert u2.profile in qs2
    assert u1.profile not in qs2


@pytest.mark.django_db
def test_is_never_global():
    user = UserFactory()
    is_own_profile = Is(lambda u: u.profile)
    assert not is_own_profile.check(user)


@pytest.mark.django_db
def test_current_user():
    u1 = UserFactory()
    u2 = UserFactory()
    assert current_user.check(u1, u1)
    assert not current_user.check(u1, u2)
    assert set(current_user.filter(u1, User.objects.all())) == {u1}
