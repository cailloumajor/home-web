# -*- coding: utf-8 -*-

import operator
from datetime import datetime, time, timedelta
from functools import reduce

from django.db.models import Q
from rest_framework import serializers

from .models import Zone, Slot, Derogation, PilotwireLog


TIME_FORMAT = '%H:%M'


def validate_quarter_hour(value):
    if value.minute % 15 != 0:
        raise serializers.ValidationError(
            "Seules les valeurs 00, 15, 30 et 45 "
            "sont autorisées pour les minutes"
        )


class OffsetTimeField(serializers.TimeField):

    def to_internal_value(self, data):
        super_time = super().to_internal_value(data)
        validate_quarter_hour(super_time)
        dt = datetime(1, 1, 2, super_time.hour, super_time.minute)
        return (dt - timedelta(minutes=1)).time()

    def to_representation(self, obj):
        if isinstance(obj, time):  # pragma: no cover
            dt = datetime(1, 1, 1, obj.hour, obj.minute)
            obj = (dt + timedelta(minutes=1)).time()
        return super().to_representation(obj)


class CustomDateTimeField(serializers.DateTimeField):

    def __init__(self, with_offset=False, *args, **kwargs):
        self.with_offset = with_offset
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        super_dt = super().to_internal_value(data)
        super_dt = super_dt.replace(second=0, microsecond=0)
        validate_quarter_hour(super_dt)
        if self.with_offset:
            super_dt = super_dt - timedelta(minutes=1)
        return super_dt

    def to_representation(self, obj):
        if isinstance(obj, datetime) and self.with_offset:
            obj = obj + timedelta(minutes=1)
        return super().to_representation(obj)


class ZoneSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Zone
        fields = ('url', 'num', 'desc')
        extra_kwargs = {
            'url': {'view_name': 'heating:zone-detail'},
        }


class SlotSerializer(serializers.HyperlinkedModelSerializer):

    end_time = OffsetTimeField(
        format=TIME_FORMAT,
        input_formats=[TIME_FORMAT],
        label=Slot._meta.get_field('end_time').verbose_name.capitalize())

    class Meta:
        model = Slot
        fields = ('url', 'id', 'zone', 'mode', 'start_time', 'end_time',
                  'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
        extra_kwargs = {
            'start_time': {
                'format': TIME_FORMAT, 'input_formats': [TIME_FORMAT]
            },
            'url': {'view_name': 'heating:slot-detail'},
            'zone': {'view_name': 'heating:zone-detail'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].validators += [validate_quarter_hour]

    def validate(self, data):
        days_on = [d for d in
                   ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
                   if data.get(d)]
        q_objects = [Q(t) for t in [(d, True) for d in days_on]]
        s_time = data.get('start_time')
        e_time = data.get('end_time')
        zone = data.get('zone')

        if not days_on:
            raise serializers.ValidationError("Aucun jour sélectionné")

        if not s_time < e_time:
            raise serializers.ValidationError(
                "L'heure de fin doit être supérieure à l'heure de début"
            )

        instance_pk = getattr(self.instance, 'pk', None)
        queryset = Slot.objects.exclude(pk=instance_pk).filter(zone=zone)
        queryset = queryset.filter(reduce(operator.or_, q_objects))
        queryset = queryset.filter(
            (Q(start_time__lte=s_time) & Q(end_time__gte=s_time)) |
            (Q(start_time__lte=e_time) & Q(end_time__gte=e_time)) |
            (Q(start_time__gte=s_time) & Q(end_time__lte=e_time)))
        if queryset.exists():
            raise serializers.ValidationError(
                "Les horaires sont en conflit avec un créneau existant"
            )

        return data


class DerogationSerializer(serializers.HyperlinkedModelSerializer):

    start_dt = CustomDateTimeField()
    end_dt = CustomDateTimeField(with_offset=True)
    start_initial = serializers.DateTimeField(write_only=True)
    active = serializers.BooleanField(read_only=True, source='is_active')
    outdated = serializers.BooleanField(read_only=True, source='is_outdated')

    class Meta:
        model = Derogation
        fields = ('url', 'id', 'mode', 'creation_dt', 'start_dt', 'end_dt',
                  'zones', 'start_initial', 'active', 'outdated')
        extra_kwargs = {
            'url': {'view_name': 'heating:derogation-detail'},
            'zones': {'view_name': 'heating:zone-detail'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self.instance, Derogation):
            del self.fields['start_initial']

    def create(self, validated_data):
        del validated_data['start_initial']
        return super().create(validated_data)

    def validate(self, data):
        start_initial = data.get('start_initial')
        start_dt = data['start_dt']
        end_dt = data['end_dt']

        if start_initial and start_dt < start_initial:
            raise serializers.ValidationError({
                'start_dt':
                "La prise d'effet ne doit pas se situer dans le passé"
            })

        if not start_dt < end_dt:
            raise serializers.ValidationError({
                'end_dt':
                "La fin d'effet doit être ultérieure à la prise d'effet"
            })

        instance_pk = getattr(self.instance, 'pk', None)
        queryset = Derogation.objects.exclude(pk=instance_pk)
        queryset = queryset.filter(zones__in=data['zones'])
        queryset = queryset.filter(
            (Q(start_dt__lte=start_dt) & Q(end_dt__gte=start_dt)) |
            (Q(start_dt__lte=end_dt) & Q(end_dt__gte=end_dt)) |
            (Q(start_dt__gte=start_dt) & Q(end_dt__lte=end_dt))
        )
        if queryset.exists():
            raise serializers.ValidationError(
                "Les horaires sont en conflit avec une dérogation existante"
            )

        return data


class PilotwireLogSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = PilotwireLog
        fields = ('url', 'id', 'timestamp', 'level', 'message')
        extra_kwargs = {
            'url': {'view_name': 'heating:pilotwirelog-detail'},
        }
