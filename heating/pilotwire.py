# -*- coding: utf-8 -*-

import logging
from functools import wraps
from pprint import pformat

from django.conf import settings
from django.core.mail import mail_admins

from celery import shared_task
from celery.exceptions import Ignore
from pilotwire_controller.client import \
    ControllerProxy, PilotwireModesInconsistent
from redis import StrictRedis

from .models import Zone


logger = logging.getLogger(__name__)

REDIS_KEY = 'pilotwire_controller:status'
PILOTWIRE_IP_PORT = '{}:{}'.format(
    settings.PILOTWIRE_IP, settings.PILOTWIRE_PORT
)


def needs_settings(needed_settings):
    def _decorator(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            missing = [s for s in needed_settings if not getattr(settings, s)]
            if not missing:
                return func(*args, **kwargs)
            from celery import current_task
            if current_task and current_task.request.id:
                raise Ignore(
                    "Missing {} setting(s)".format(", ".join(missing))
                )
        return _wrapper
    return _decorator


@needs_settings(['REDIS_URL'])
def is_active():
    redis = StrictRedis.from_url(settings.REDIS_URL)
    return redis.get(REDIS_KEY) == b'active'


@shared_task(ignore_result=True)
@needs_settings(['REDIS_URL', 'PILOTWIRE_IP', 'PILOTWIRE_PORT'])
def update_status():
    redis = StrictRedis.from_url(settings.REDIS_URL)
    pwclient = ControllerProxy(PILOTWIRE_IP_PORT)

    old_status = redis.get(REDIS_KEY)
    if old_status is not None:
        old_status = old_status.decode()

    status = pwclient.check_status()
    redis.set(REDIS_KEY, status, ex=90)

    if status != old_status:
        log_message = "Pilotwire controller status changed from {} to {}"
        log_message = log_message.format(old_status, status)
        if status == 'active':
            log_message += ", going to set pilotwire modes"
            logger.info(log_message)
            set_modes()
        else:
            logger.error(log_message)
            mail_admins("Pilotwire controller connection error", log_message)


@shared_task(ignore_result=True)
@needs_settings(['PILOTWIRE_IP', 'PILOTWIRE_PORT'])
def set_modes():
    if not is_active():
        return

    modes = Zone.objects.get_modes()
    client = ControllerProxy(PILOTWIRE_IP_PORT)

    try:
        client.modes = modes
    except PilotwireModesInconsistent as pwerr:
        logger.error(pwerr)
        return

    logger.info(
        "Modes set on pilotwire controller : %s", pformat(client.modes)
    )
