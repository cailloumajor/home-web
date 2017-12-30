# pylint: disable=no-self-use, redefined-outer-name, too-few-public-methods
# pylint: disable=no-member

import random
from collections import namedtuple
from datetime import datetime, time, timedelta
from itertools import chain

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

import pytest
from django_dynamic_fixture import F, G
from django_dynamic_fixture.fixture_algorithms import random_fixture
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from ..models import Zone, Slot, Derogation, PilotwireLog
from ..serializers import ZoneSerializer, SlotSerializer, \
    DerogationSerializer, PilotwireLogSerializer


PREFIX = 'heating:'
LIST_SUFFIX = '-list'
DETAIL_SUFFIX = '-detail'

ZONE_CREATE_DATA = {'num': 2}
SLOT_CREATE_DATA = {
    'start_time': time(9, 30),
    'end_time': time(16, 14),
    'mon': True
}
DEROGATION_CREATE_DATA = {
    'zones': [F(num=1), F(num=2)],
    'start_dt': datetime(2016, 9, 14, 21, 30, tzinfo=timezone.utc),
    'end_dt': datetime(2016, 9, 14, 21, 44, tzinfo=timezone.utc)
}


class CustomDataFixture(random_fixture.RandomDataFixture):

    def timefield_config(self, field, key):
        return (
            timezone.now() - timedelta(seconds=random.randint(1, 36500))
        ).time()


def model_to_dict(instance):
    """
    Modified version of django.forms.models.model_to_dict.
    Same behavior excluding many to many fields.
    """
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields):
        if not getattr(f, 'editable', False):
            continue
        data[f.name] = f.value_from_object(instance)
    return data


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def pk_fieldname(params):
    return params.model._meta.pk.name


@pytest.fixture
def serialize(params, client):
    def inner_serializer(instance):
        request = client.request().wsgi_request
        serializer = params.serializer(instance, context={'request': request})
        return serializer.data
    return inner_serializer


Parameters = namedtuple('Parameters', [
    'base_name', 'model', 'serializer', 'create_data', 'other_data',
    'read_only'
])


@pytest.mark.django_db
@pytest.mark.parametrize('params', [
    Parameters('zone', Zone, ZoneSerializer, ZONE_CREATE_DATA, {}, True),
    Parameters('slot', Slot, SlotSerializer, SLOT_CREATE_DATA, {}, False),
    Parameters('derogation', Derogation, DerogationSerializer,
               DEROGATION_CREATE_DATA, {'start_initial': "2016-09-12T23:01"},
               False),
    Parameters('pilotwirelog', PilotwireLog, PilotwireLogSerializer,
               {}, {}, True)
], ids=lambda p: p.model.__name__)
class TestModelAPI:

    def test_list_api(self, client, params):
        view_name = PREFIX + params.base_name + LIST_SUFFIX
        url = reverse(view_name)
        G(params.model, n=2)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_detail_api(self, client, params, pk_fieldname):
        instance = G(params.model, data_fixture=CustomDataFixture())
        view_name = PREFIX + params.base_name + DETAIL_SUFFIX
        url = reverse(view_name, args=[instance.pk])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        expected_fields = model_to_dict(instance).keys()
        assert response.data.keys() >= expected_fields
        assert response.data[pk_fieldname] == getattr(instance, pk_fieldname)

    def test_create_api(self, client, params, pk_fieldname, serialize):
        view_name = PREFIX + params.base_name + LIST_SUFFIX
        url = reverse(view_name)
        new = G(params.model, data_fixture=CustomDataFixture(),
                **params.create_data)
        new_dict = model_to_dict(new)
        del new_dict[pk_fieldname]
        new_data = serialize(new)
        new_data.update(params.other_data)
        params.model.objects.get(pk=new.pk).delete()
        response = client.post(url, new_data)
        if params.read_only:
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
            return
        assert response.status_code == status.HTTP_201_CREATED
        assert isinstance(params.model.objects.get(**new_dict), params.model)

    def test_delete_api(self, client, params):
        instance = G(params.model, data_fixture=CustomDataFixture())
        view_name = PREFIX + params.base_name + DETAIL_SUFFIX
        url = reverse(view_name, args=[instance.pk])
        response = client.delete(url)
        if params.read_only:
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
            return
        assert response.status_code == status.HTTP_204_NO_CONTENT
        with pytest.raises(ObjectDoesNotExist):
            params.model.objects.get(pk=instance.pk)

    def test_update_api(self, client, params, pk_fieldname, serialize):
        instance = G(params.model, data_fixture=CustomDataFixture())
        view_name = PREFIX + params.base_name + DETAIL_SUFFIX
        url = reverse(view_name, args=[instance.pk])
        new = G(params.model, data_fixture=CustomDataFixture(),
                **params.create_data)
        new_dict = model_to_dict(new)
        new_dict[pk_fieldname] = getattr(instance, pk_fieldname)
        new_data = serialize(new)
        new_data[pk_fieldname] = getattr(instance, pk_fieldname)
        params.model.objects.get(pk=new.pk).delete()
        response = client.patch(url, new_data)
        if params.read_only:
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
            return
        assert response.status_code == status.HTTP_200_OK
        new_instance = params.model.objects.get(pk=instance.pk)
        assert model_to_dict(new_instance) == new_dict
