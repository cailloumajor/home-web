# -*- coding: utf-8 -*-

import logging


class PilotwireHandler(logging.Handler):

    def __init__(self, logLength):
        super(PilotwireHandler, self).__init__()
        self.log_length = logLength

    def emit(self, record):
        from .models import PilotwireLog
        PilotwireLog.objects.create(
            level=record.levelname, message=record.getMessage())
        if PilotwireLog.objects.count() > self.log_length:
            to_delete = PilotwireLog.objects.all()[self.log_length:]
            PilotwireLog.objects.filter(pk__in=to_delete).delete()
