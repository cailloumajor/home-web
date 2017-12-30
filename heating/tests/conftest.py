import pytest
from redislite import StrictRedis
from redislite.patch import patch_redis, unpatch_redis


REDIS_DB_FILE = '/tmp/redis.db'


@pytest.fixture
def patched_redis(settings):
    patch_redis(REDIS_DB_FILE)
    _redis = StrictRedis(REDIS_DB_FILE)
    settings.REDIS_URL = 'unix://{}'.format(_redis.socket_file)
    _redis.flushall()
    yield _redis
    unpatch_redis()
