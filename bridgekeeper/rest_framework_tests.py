import json

import pytest
from bridgekeeper import perms
from bridgekeeper.rules import Attribute, always_allow, always_deny
from django.core.exceptions import ImproperlyConfigured
from rest_framework.serializers import ModelSerializer
from rest_framework.test import APIRequestFactory as RequestFactory
from rest_framework.viewsets import ModelViewSet
from shrubberies import factories, models

from .rest_framework import RuleFilter, RulePermissions


class StoreSerializer(ModelSerializer):
    class Meta:
        model = models.Store
        fields = "__all__"


class StoreViewSet(ModelViewSet):
    queryset = models.Store.objects.all()
    permission_classes = (RulePermissions,)
    filter_backends = (RuleFilter,)
    serializer_class = StoreSerializer


@pytest.mark.django_db
def test_list_view_is_filtered():
    user = factories.UserFactory()
    s1 = factories.StoreFactory(name="a")
    factories.StoreFactory(name="b")
    perms["shrubberies.view_store"] = Attribute("name", "a")

    v = StoreViewSet.as_view({"get": "list"})
    r = RequestFactory().get("/", HTTP_CONTENT_TYPE="text/json")
    r.user = user
    response = v(r)
    response.render()
    print(response.content)
    assert response.status_code == 200
    data = json.loads(response.content.decode("utf8"))
    assert len(data) == 1
    assert data[0]["id"] == s1.id


@pytest.mark.django_db
def test_list_view_is_disallowed_if_not_possible():
    user = factories.UserFactory()
    perms["shrubberies.view_store"] = always_deny

    v = StoreViewSet.as_view({"get": "list"})
    r = RequestFactory().get("/", HTTP_CONTENT_TYPE="text/json")
    r.user = user
    response = v(r)
    assert response.status_code == 403


@pytest.mark.django_db
def test_detail_view_ok_when_permitted():
    user = factories.UserFactory()
    s1 = factories.StoreFactory(name="a")
    factories.StoreFactory(name="b")
    perms["shrubberies.view_store"] = Attribute("name", "a")

    v = StoreViewSet.as_view({"get": "retrieve"})
    r = RequestFactory().get("/", HTTP_CONTENT_TYPE="text/json")
    r.user = user
    response = v(r, pk=s1.id)
    assert response.status_code == 200


@pytest.mark.django_db
def test_detail_view_404_when_not_permitted():
    user = factories.UserFactory()
    factories.StoreFactory(name="a")
    s2 = factories.StoreFactory(name="b")
    perms["shrubberies.view_store"] = Attribute("name", "a")

    v = StoreViewSet.as_view({"get": "retrieve"})
    r = RequestFactory().get("/", HTTP_CONTENT_TYPE="text/json")
    r.user = user
    response = v(r, pk=s2.id)
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_view_ok_when_permitted():
    user = factories.UserFactory()
    s1 = factories.StoreFactory(name="a")
    factories.StoreFactory(name="b")
    perms["shrubberies.view_store"] = Attribute("name", "a")
    perms["shrubberies.change_store"] = Attribute("name", "a")

    v = StoreViewSet.as_view({"patch": "partial_update"})
    r = RequestFactory().patch("/", {"name": "a"}, HTTP_CONTENT_TYPE="text/json")
    r.user = user
    response = v(r, pk=s1.id)
    assert response.status_code == 200


@pytest.mark.django_db
def test_update_view_404_when_not_permitted():
    user = factories.UserFactory()
    factories.StoreFactory(name="a")
    s2 = factories.StoreFactory(name="b")
    perms["shrubberies.view_store"] = Attribute("name", "a")
    perms["shrubberies.change_store"] = Attribute("name", "a")

    v = StoreViewSet.as_view({"patch": "partial_update"})
    r = RequestFactory().patch("/", {"name": "a"}, HTTP_CONTENT_TYPE="text/json")
    r.user = user
    response = v(r, pk=s2.id)
    response.render()
    print(response.content)
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_view_403_when_read_only():
    user = factories.UserFactory()
    factories.StoreFactory(name="a")
    s2 = factories.StoreFactory(name="b")
    perms["shrubberies.view_store"] = always_allow
    perms["shrubberies.change_store"] = Attribute("name", "a")

    v = StoreViewSet.as_view({"patch": "partial_update"})
    r = RequestFactory().patch("/", {"name": "a"}, HTTP_CONTENT_TYPE="text/json")
    r.user = user
    response = v(r, pk=s2.id)
    assert response.status_code == 403


@pytest.mark.django_db
def test_improperly_configured_when_perm_missing():
    user = factories.UserFactory()
    s1 = factories.StoreFactory(name="a")
    factories.StoreFactory(name="b")

    v = StoreViewSet.as_view({"get": "retrieve"})
    r = RequestFactory().get("/", HTTP_CONTENT_TYPE="text/json")
    r.user = user
    with pytest.raises(ImproperlyConfigured):
        v(r, pk=s1.id)
