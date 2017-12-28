# -*- coding: utf-8 -*-

from rest_framework import routers

from .views import ZoneViewSet, SlotViewSet, \
    DerogationViewSet, PilotwireLogViewSet


router = routers.DefaultRouter()
router.register(r'zones', ZoneViewSet)
router.register(r'slots', SlotViewSet)
router.register(r'derogations', DerogationViewSet)
router.register(r'pilotwirelog', PilotwireLogViewSet)

app_name = 'heating'
urlpatterns = router.urls
