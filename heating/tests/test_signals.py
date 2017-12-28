# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name, no-self-use, no-member

from datetime import timedelta

from django.utils import timezone

import pytest
from django_dynamic_fixture import G

from .. import tasks
from ..models import Derogation


pytestmark = pytest.mark.usefixtures('disable_receiver')


@pytest.fixture
def disable_receiver(monkeypatch):
    """Disables signal receiver decorator.
    This ensures that signals are connected before using this fixture,
    and not when the mocker imports the signals module."""
    def noop_receiver(*_, **__):
        def _decorator(func):
            return func
        return _decorator
    monkeypatch.setattr('django.dispatch.receiver', noop_receiver)


@pytest.fixture
def needed_settings(settings, patched_redis):
    settings.CELERY_BROKER_URL = 'redis+socket://{}'.format(
        patched_redis.socket_file)
    settings.PILOTWIRE_IP = '0.0.0.0'
    settings.PILOTWIRE_PORT = 1
    patched_redis.set(tasks.pilotwire.REDIS_KEY, 'active')


@pytest.fixture
def set_modes_mock(mocker):
    return mocker.patch('heating.signals.tasks.pilotwire.set_modes.delay')


@pytest.mark.django_db
@pytest.mark.usefixtures('needed_settings')
class TestActiveDerogationHandler:

    def test_no_celery_broker_url_setting(self, settings, set_modes_mock):
        settings.CELERY_BROKER_URL = None
        G(Derogation,
          start_dt=timezone.now()-timedelta(minutes=5),
          end_dt=timezone.now()+timedelta(minutes=5))
        assert not set_modes_mock.called

    def test_pilotwire_not_active(self, patched_redis, set_modes_mock):
        patched_redis.set(tasks.pilotwire.REDIS_KEY, 'not_active_for_testing')
        G(Derogation,
          start_dt=timezone.now()-timedelta(minutes=5),
          end_dt=timezone.now()+timedelta(minutes=5))
        assert not set_modes_mock.called

    def test_not_active_derogation(self, set_modes_mock):
        G(Derogation,
          start_dt=timezone.now()-timedelta(minutes=5),
          end_dt=timezone.now()-timedelta(minutes=2))
        assert not set_modes_mock.called

    def test_active_derogation(self, set_modes_mock, caplog):
        message = "Active derogation {}, going to set pilotwire modes"
        derog = G(Derogation,
                  start_dt=timezone.now()-timedelta(minutes=5),
                  end_dt=timezone.now()+timedelta(minutes=5))
        assert set_modes_mock.call_count == 1
        assert caplog.records[-1].message == message.format('created')
        set_modes_mock.reset_mock()
        derog.save()
        assert set_modes_mock.call_count == 1
        assert caplog.records[-1].message == message.format('changed')
        set_modes_mock.reset_mock()
        derog.delete()
        assert set_modes_mock.call_count == 1
        assert caplog.records[-1].message == message.format('removed')
