from ..settings import CeleryBrokerURLValue


def test_celery_broker_url_value(monkeypatch):
    monkeypatch.setenv('DJANGO_TEST', 'redis://localhost')
    assert CeleryBrokerURLValue(environ_name='TEST') == (
        'redis://localhost'
    )
    monkeypatch.setenv('DJANGO_TEST', 'unix://localhost')
    assert CeleryBrokerURLValue(environ_name='TEST') == (
        'redis+socket://localhost'
    )
