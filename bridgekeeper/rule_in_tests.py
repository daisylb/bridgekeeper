import pytest
from django.contrib.auth.models import Group
from shrubberies.factories import ShrubberyFactory, UserFactory
from shrubberies.models import Shrubbery

from .rules import In, in_current_groups


@pytest.mark.django_db
def test_in_user_function_returning_qs():
    u1 = UserFactory()
    u2 = UserFactory()
    s_in_1 = ShrubberyFactory(branch=u1.profile.branch)
    s_in_2 = ShrubberyFactory(branch=u1.profile.branch)
    s_out_1 = ShrubberyFactory(branch=u2.profile.branch)
    s_out_2 = ShrubberyFactory(branch=u2.profile.branch)
    is_in_branch = In(lambda u: u.profile.branch.shrubbery_set.all())

    assert is_in_branch.check(u1, s_in_1)
    assert is_in_branch.check(u1, s_in_2)
    assert not is_in_branch.check(u1, s_out_1)
    assert not is_in_branch.check(u1, s_out_2)

    qs1 = is_in_branch.filter(u1, Shrubbery.objects.all())
    qs2 = is_in_branch.filter(u2, Shrubbery.objects.all())
    assert set(qs1) == {s_in_1, s_in_2}
    assert set(qs2) == {s_out_1, s_out_2}


@pytest.mark.django_db
def test_is_never_global():
    user = UserFactory()
    is_in_branch = In(lambda u: u.profile.branch.shrubbery_set.all())
    assert not is_in_branch.check(user)


@pytest.mark.django_db
def test_in_current_groups():
    user = UserFactory()
    g_in_1 = Group.objects.create(name="g_in_1")
    g_in_2 = Group.objects.create(name="g_in_2")
    g_out_1 = Group.objects.create(name="g_out_1")
    Group.objects.create(name="g_out_2")
    user.groups.set((g_in_1, g_in_2))
    user.save()

    assert in_current_groups.check(user, g_in_1)
    assert not in_current_groups.check(user, g_out_1)

    assert set(in_current_groups.filter(user, Group.objects.all())) == {g_in_1, g_in_2}
