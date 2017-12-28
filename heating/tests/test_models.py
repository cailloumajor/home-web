# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, redefined-outer-name, too-few-public-methods
# pylint: disable=unused-argument, no-member

import datetime

from django.utils import timezone

from django_dynamic_fixture import G, N, F
import pytest

from ..models import Zone, Slot, Derogation, PilotwireLog


WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


@pytest.fixture
def now():
    return timezone.localtime(timezone.now())


@pytest.fixture
def today(now):
    today_weekday = now.weekday()
    return WEEKDAYS[today_weekday]


@pytest.fixture
def patch_now(monkeypatch):
    fake_now = datetime.datetime(2016, 8, 27, 14, 9, 43, 0)
    fake_now = timezone.make_aware(fake_now)
    monkeypatch.setattr('django.utils.timezone.now', lambda: fake_now)


@pytest.fixture
def derogation_fixture(db):
    class Fixture:
        def __init__(self):
            self.past_derog = G(
                Derogation,
                start_dt=timezone.now() - datetime.timedelta(days=1),
                end_dt=timezone.now() - datetime.timedelta(minutes=2)
            )
            self.active_derog = G(
                Derogation,
                start_dt=timezone.now(),
                end_dt=timezone.now() + datetime.timedelta(minutes=2)
            )
            self.future_derog = G(
                Derogation,
                start_dt=timezone.now() + datetime.timedelta(minutes=2),
                end_dt=timezone.now() + datetime.timedelta(days=1)
            )
    return Fixture()


class TestZoneModel:

    def test_string_representation(self):
        zone = N(Zone)
        assert str(zone) == 'Z{}'.format(zone.num)

    @pytest.mark.django_db
    def test_get_modes_queryset_method(self, now, today):
        # Create an empty zone 1
        G(Zone, num=1)
        # Create an active slot in zone 2
        G(Slot, zone=F(num=2), **{today: True}, mode='E',
          start_time=(now - datetime.timedelta(minutes=2)).time(),
          end_time=(now + datetime.timedelta(minutes=2)).time())
        # Create an active slot in zone 3
        G(Slot, zone=F(num=3), **{today: True}, mode='H',
          start_time=(now - datetime.timedelta(minutes=2)).time(),
          end_time=(now + datetime.timedelta(minutes=2)).time())
        # Create an active derogation in zone 3
        G(Derogation, mode='A', zones=[F(num=3)],
          start_dt=timezone.now() - datetime.timedelta(minutes=2),
          end_dt=timezone.now() + datetime.timedelta(minutes=2))
        assert Zone.objects.get_modes() == {'1': 'C', '2': 'E', '3': 'A'}


class TestSlotModel:

    @pytest.mark.django_db
    def test_string_representation(self):
        slot = N(
            Slot, mon=True, wed=True, fri=True, sun=True, mode='E',
            start_time=datetime.time(4, 2), end_time=datetime.time(15, 54)
        )
        expected = "Z{} 04:02:00-15:54:00 [L*M*V*D] Eco".format(slot.zone.num)
        assert str(slot) == expected

    @pytest.mark.django_db
    def test_active_queryset_method(self, patch_now, now, today):
        all_but_today = {day: True for day in
                         [wd for wd in WEEKDAYS if wd != today]}
        zone = G(Zone, num=1)
        # Create a past slot
        G(Slot, zone=zone, **{today: True},
          start_time=(now - datetime.timedelta(hours=1)).time(),
          end_time=(now - datetime.timedelta(minutes=2)).time())
        # Create an active slot
        active_slot = G(
            Slot, zone=zone, **{today: True},
            start_time=(now - datetime.timedelta(minutes=2)).time(),
            end_time=(now + datetime.timedelta(minutes=2)).time())
        # Create a future slot
        G(Slot, zone=zone, **{today: True},
          start_time=(now + datetime.timedelta(minutes=2)).time(),
          end_time=(now + datetime.timedelta(hours=1)).time())
        # Create a slot active `all but today` days of week at the same time
        G(Slot, zone=zone, **all_but_today,
          start_time=now.time(),
          end_time=(now + datetime.timedelta(minutes=2)).time())
        queryset = Slot.objects.active()
        assert queryset.count() == 1
        assert queryset[0] == active_slot


class TestDerogationModel:

    @pytest.mark.django_db
    def test_string_representation(self):
        start = timezone.make_aware(
            datetime.datetime(2015, 2, 25, 17, 24),
            timezone.get_default_timezone()
        )
        end = timezone.make_aware(
            datetime.datetime(2015, 3, 18, 18, 12),
            timezone.get_default_timezone()
        )
        derog = G(Derogation, start_dt=start, end_dt=end, mode='H',
                  zones=[F(num=2), F(num=3)])
        assert str(derog) == "25/02-17:24->18/03-18:12 H Z2-Z3"

    def test_active_queryset_method(self, derogation_fixture):
        queryset = Derogation.objects.active()
        assert queryset.count() == 1
        assert queryset[0] == derogation_fixture.active_derog

    def test_is_active_model_method(self, derogation_fixture):
        assert not derogation_fixture.past_derog.is_active()
        assert derogation_fixture.active_derog.is_active()
        assert not derogation_fixture.future_derog.is_active()

    def test_is_outdated_model_method(self, derogation_fixture):
        assert derogation_fixture.past_derog.is_outdated()
        assert not derogation_fixture.active_derog.is_outdated()
        assert not derogation_fixture.future_derog.is_outdated()


class TestPilotwireLogModel:

    @pytest.mark.parametrize(['message', 'expected'], [
        ('012345678901234567890123456789', '012345678901234567890123456789'),
        ('0123456789012345678901234567890',
         '012345678901234567890123456789...')
    ], ids=["Less than 30 characters", "More than 30 characters"])
    def test_string_representation(self, message, expected):
        record = N(PilotwireLog, message=message)
        assert str(record) == "{} - {} - {}".format(
            timezone.localtime(record.timestamp).strftime("%Y.%m.%d %H:%M:%S"),
            record.level, expected)
