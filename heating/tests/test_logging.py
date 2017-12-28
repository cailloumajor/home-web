# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, redefined-outer-name

import logging

import pytest

from ..models import PilotwireLog


@pytest.fixture
def logger():
    return logging.getLogger('pilotwire_testing_logger')


@pytest.mark.usefixtures('db')
class TestPilotwireLogging:

    @pytest.mark.parametrize('level', list(range(20, 51, 10)),
                             ids=logging.getLevelName)
    def test_logging(self, logger, level):
        lvl_name = logging.getLevelName(level)
        message = "Test level {} - {}".format(level, lvl_name)
        logger.log(level, message)
        lastlog = PilotwireLog.objects.all()[0]
        assert lastlog.level == lvl_name
        assert lastlog.message == message

    def test_max_log_length(self, logger):
        for i in range(6):
            logger.critical("Log entry #{}".format(i))
        assert PilotwireLog.objects.count() == 5
