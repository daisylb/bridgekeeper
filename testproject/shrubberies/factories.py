from decimal import Decimal

import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory

from . import models


class StoreFactory(DjangoModelFactory):
    name = factory.Faker("company")

    class Meta:
        model = models.Store


class BranchFactory(DjangoModelFactory):
    name = factory.Faker("city")
    store = factory.SubFactory(StoreFactory)

    class Meta:
        model = models.Branch


class ProfileFactory(DjangoModelFactory):
    branch = factory.SubFactory(BranchFactory)
    role = "shrubber"
    user = factory.SubFactory("shrubberies.factories.UserFactory")

    class Meta:
        model = models.Profile


class ShrubberyFactory(DjangoModelFactory):
    name = factory.Faker("catch_phrase")
    price = Decimal("14.99")
    branch = factory.SubFactory(BranchFactory)

    class Meta:
        model = models.Shrubbery


class UserFactory(DjangoModelFactory):
    username = factory.Faker("user_name")
    email = factory.Faker("email")
    profile = factory.RelatedFactory(ProfileFactory, "user")

    class Meta:
        model = User
