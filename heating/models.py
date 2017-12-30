from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from .managers import ZoneManager, SlotQuerySet, DerogationQuerySet


class Zone(models.Model):

    num = models.PositiveSmallIntegerField(
        verbose_name="numéro de zone",
        primary_key=True,
        validators=[MinValueValidator(1), MaxValueValidator(4)])
    desc = models.CharField(
        verbose_name="description",
        max_length=50,
        blank=True)
    objects = ZoneManager()

    class Meta:
        ordering = ['num']

    def __str__(self):
        return 'Z{}'.format(self.num)


class ModeBase(models.Model):

    MODE_CHOICES = (
        ('E', 'Eco'),
        ('H', 'Hors gel'),
        ('A', 'Arrêt'),
    )
    mode = models.CharField(
        max_length=1,
        verbose_name="mode de fonctionnement",
        choices=MODE_CHOICES,
    )

    class Meta:
        abstract = True


class Slot(ModeBase):

    zone = models.ForeignKey(Zone, models.CASCADE)
    mon = models.BooleanField(verbose_name="lundi", default=False)
    tue = models.BooleanField(verbose_name="mardi", default=False)
    wed = models.BooleanField(verbose_name="mercredi", default=False)
    thu = models.BooleanField(verbose_name="jeudi", default=False)
    fri = models.BooleanField(verbose_name="vendredi", default=False)
    sat = models.BooleanField(verbose_name="samedi", default=False)
    sun = models.BooleanField(verbose_name="dimanche", default=False)
    start_time = models.TimeField(verbose_name="heure de début")
    end_time = models.TimeField(verbose_name="heure de fin")
    objects = SlotQuerySet.as_manager()

    def __str__(self):
        days_fields_list = [
            self.mon, self.tue, self.wed, self.thu,
            self.fri, self.sat, self.sun
        ]
        days_string = ''.join(
            [d if b else '*' for (d, b) in zip('LMMJVSD', days_fields_list)]
        )
        return "{} {}-{} [{}] {}".format(
            self.zone, self.start_time,
            self.end_time, days_string,
            self.get_mode_display()
        )


class Derogation(ModeBase):

    creation_dt = models.DateTimeField(
        verbose_name="date/heure de création", auto_now_add=True
    )
    start_dt = models.DateTimeField(verbose_name="prise d'effet")
    end_dt = models.DateTimeField(verbose_name="fin d'effet")
    zones = models.ManyToManyField(Zone)
    objects = DerogationQuerySet.as_manager()

    class Meta():
        ordering = ['creation_dt']

    def __str__(self):
        def dt_conv(dt):
            return timezone.localtime(dt).strftime('%d/%m-%H:%M')
        return "{}->{} {} {}".format(
            dt_conv(self.start_dt), dt_conv(self.end_dt), self.mode,
            '-'.join([str(z) for z in self.zones.all()])
        )

    def is_active(self):
        now = timezone.now()
        return self.start_dt <= now and self.end_dt >= now

    def is_outdated(self):
        return self.end_dt < timezone.now()


class PilotwireLog(models.Model):

    timestamp = models.DateTimeField(
        verbose_name="date/heure",
        auto_now_add=True,
        db_index=True)
    level = models.CharField(verbose_name="niveau", max_length=10)
    message = models.TextField()

    class Meta():
        ordering = ['-timestamp']

    def __str__(self):
        msg = (self.message[:30] + '...' if len(self.message) > 30
               else self.message)
        return "{} - {} - {}".format(
            timezone.localtime(self.timestamp).strftime("%Y.%m.%d %H:%M:%S"),
            self.level, msg
        )
