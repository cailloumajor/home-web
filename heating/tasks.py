from datetime import timedelta

from django.core.mail import mail_admins
from django.utils import timezone

from celery import shared_task

from . import pilotwire
from .models import Derogation


# Avoid 'unused import' linter warning
__dummy__ = pilotwire


@shared_task(ignore_result=True)
def clearoldderogations(days):
    deadline = timezone.now() - timedelta(days=days)
    queryset = Derogation.objects.filter(end_dt__lte=deadline)
    count = queryset.count()
    removed = [str(d) for d in queryset]
    queryset.delete()

    message = "{} derogation(s) removed :\n".format(count)
    message += '\n'.join(removed)
    mail_admins("Old derogations cleaning", message)
