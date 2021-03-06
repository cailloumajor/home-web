# -*- coding: utf-8 -*-

from django.contrib import admin
from .models import Zone


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('num', 'desc')
