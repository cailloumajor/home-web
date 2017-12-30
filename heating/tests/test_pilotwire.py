# pylint: disable=no-self-use

from collections import namedtuple

import pytest
from pilotwire_controller.client import PilotwireModesInconsistent

from .. import tasks


STATUS_MSG = [
    "Pilotwire controller status changed from {} to {}",
    ", going to set pilotwire modes"
]


class FakeControllerProxy:

    TEST_TYPE = 'undefined'

    def __init__(self, _):
        self.count = 0

    def check_status(self):
        if self.TEST_TYPE.startswith('status_'):
            return self.TEST_TYPE[7:]

    @property
    def modes(self):
        return {
            '2': 'A',
            '1': 'Z',
        }

    @modes.setter
    def modes(self, _):
        if self.TEST_TYPE == 'modes_inconsistent':
            raise PilotwireModesInconsistent("Inconsistent test")
        else:
            return


@pytest.fixture
def pilotwire_settings(settings):
    settings.PILOTWIRE_IP = '0.0.0.0'
    settings.PILOTWIRE_PORT = 1


pytestmark = pytest.mark.usefixtures('pilotwire_settings')


@pytest.fixture
def set_is_active(monkeypatch):
    monkeypatch.setattr(tasks.pilotwire, 'is_active', lambda: True)


def missing_settings_parametrize(missing_settings):
    return pytest.mark.parametrize(
        'setting', missing_settings, ids=lambda s: "missing " + s
    )


Params = namedtuple('Params', [
    'test_type', 'level', 'message'
])


@pytest.mark.parametrize('params', [
    Params(
        'all_ok', 'INFO',
        "Modes set on pilotwire controller : {'1': 'Z', '2': 'A'}"
    ),
    Params('modes_inconsistent', 'ERROR', "Inconsistent test"),
], ids=lambda p: p.test_type)
@pytest.mark.django_db
@pytest.mark.usefixtures('set_is_active')
def test_set_modes_with_is_active_true(params, monkeypatch, caplog):
    FakeControllerProxy.TEST_TYPE = params.test_type
    monkeypatch.setattr(tasks.pilotwire, 'ControllerProxy',
                        FakeControllerProxy)
    tasks.pilotwire.set_modes()
    record = caplog.records[0]
    assert record.levelname == params.level
    assert record.message == params.message


def test_set_modes_with_is_active_false(caplog):
    tasks.pilotwire.set_modes()
    assert not caplog.records


def test_is_active(patched_redis):
    assert not tasks.pilotwire.is_active()
    patched_redis.set(tasks.pilotwire.REDIS_KEY, 'undefined')
    assert not tasks.pilotwire.is_active()
    patched_redis.set(tasks.pilotwire.REDIS_KEY, 'active')
    assert tasks.pilotwire.is_active()


Params = namedtuple('Params', [
    'keyval', 'test_type', 'exp_msg'
])


@pytest.mark.parametrize('params', [
    Params(None, 'status_active', STATUS_MSG[0] + STATUS_MSG[1]),
    Params('active', 'status_error', STATUS_MSG[0]),
    Params('undefined', 'status_undefined', None),
], ids=lambda p: "{} -> {}".format(p.keyval, p.test_type[7:]))
@pytest.mark.django_db
def test_update_status(caplog, monkeypatch, patched_redis, params, mailoutbox):
    new_status = params.test_type[7:]
    FakeControllerProxy.TEST_TYPE = params.test_type
    monkeypatch.setattr(tasks.pilotwire, 'ControllerProxy',
                        FakeControllerProxy)
    patched_redis.set(tasks.pilotwire.REDIS_KEY, params.keyval,
                      xx=True if params.keyval is None else False)
    tasks.pilotwire.update_status()
    assert patched_redis.get(tasks.pilotwire.REDIS_KEY) == new_status.encode()
    assert 0 < patched_redis.ttl(tasks.pilotwire.REDIS_KEY) <= 90
    log_filtered = [r for r in caplog.records if r.name == 'heating.pilotwire']
    if params.exp_msg:
        expected = params.exp_msg.format(params.keyval, new_status)
        assert log_filtered[0].levelname == (
            'INFO' if params.test_type == 'status_active' else 'ERROR')
        assert log_filtered[0].message == expected
        if params.test_type != 'status_active':
            assert mailoutbox[0].subject == (
                "[Django] Pilotwire controller connection error")
            assert expected in mailoutbox[0].body
    else:
        assert log_filtered == []


@pytest.mark.celery(task_always_eager=True)
@pytest.mark.usefixtures('celery_worker')
class TestMissingSettings:

    @pytest.mark.usefixtures('patched_redis')
    @missing_settings_parametrize(['REDIS_URL'])
    def test_is_active(self, setting, settings):
        setattr(settings, setting, None)
        assert tasks.pilotwire.is_active() is None

    @pytest.mark.usefixtures('patched_redis')
    @missing_settings_parametrize(
        ['REDIS_URL', 'PILOTWIRE_IP', 'PILOTWIRE_PORT']
    )
    def test_update_status(self, setting, settings, caplog):
        setattr(settings, setting, None)
        assert tasks.pilotwire.update_status() is None
        assert not caplog.records
        assert tasks.pilotwire.update_status.delay().state == 'IGNORED'

    @missing_settings_parametrize(['PILOTWIRE_IP', 'PILOTWIRE_PORT'])
    def test_set_modes(self, setting, settings, caplog):
        setattr(settings, setting, None)
        assert tasks.pilotwire.set_modes() is None
        assert not caplog.records
        assert tasks.pilotwire.set_modes.delay().state == 'IGNORED'
