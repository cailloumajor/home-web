# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-30 22:49
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('heating', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='derogation',
            name='mode',
            field=models.CharField(choices=[('E', 'Eco'), ('H', 'Hors gel'), ('A', 'Arrêt')], max_length=1, verbose_name='mode de fonctionnement'),
        ),
        migrations.AlterField(
            model_name='slot',
            name='mode',
            field=models.CharField(choices=[('E', 'Eco'), ('H', 'Hors gel'), ('A', 'Arrêt')], max_length=1, verbose_name='mode de fonctionnement'),
        ),
        migrations.AlterField(
            model_name='zone',
            name='num',
            field=models.PositiveSmallIntegerField(primary_key=True, serialize=False, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(4)], verbose_name='numéro de zone'),
        ),
    ]
