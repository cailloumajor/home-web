# -*- coding: utf-8 -*-

from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from . import tasks
from .models import Derogation


# pylint: disable=unused-argument
@receiver([post_save, post_delete],
          sender=Derogation,
          dispatch_uid='derog_pilotwire')
def active_derogation_handler(sender, **kwargs):
    if (
            not settings.CELERY_BROKER_URL or
            not tasks.pilotwire.is_active() or
            not kwargs['instance'].is_active()
    ):
        return

    created = kwargs.get('created')
    if created is not None:
        if created:
            action = 'created'
        else:
            action = 'changed'
    else:
        action = 'removed'

    tasks.pilotwire.logger.info(
        "Active derogation %s, going to set pilotwire modes", action
    )
    tasks.pilotwire.set_modes.delay()
