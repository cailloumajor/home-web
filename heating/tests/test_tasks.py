import re
from datetime import timedelta

from django.utils import timezone
from django_dynamic_fixture import G
import pytest

from ..models import Derogation
from .. import tasks


@pytest.mark.django_db
def test_clearoldderogations(mailoutbox):
    end_datetimes = (timezone.now() - timedelta(days=d) for d in range(7))
    for end_dt in end_datetimes:
        G(Derogation, end_dt=end_dt)
    tasks.clearoldderogations(4)
    assert Derogation.objects.count() == 4
    assert mailoutbox[0].subject == "[Django] Old derogations cleaning"
    assert "3 derogation(s) removed" in mailoutbox[0].body
    derog_regexp = r"[\d/\-:>]{24} [ACEH]"
    assert len(re.findall(derog_regexp, mailoutbox[0].body)) == 3
