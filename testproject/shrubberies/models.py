from django.contrib.auth.models import User
from django.db import models


class Store(models.Model):
    name = models.CharField(max_length=255)


class Branch(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)


class Shrubbery(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=5, decimal_places=2)


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    role = models.CharField(max_length=16, choices=(
        ('apprentice', 'Apprentice Shrubber'),
        ('shrubber', 'Shrubber'),
    ))
