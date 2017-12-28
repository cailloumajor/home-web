# -*- coding: utf-8 -*-
"""home_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, fmt=None):
    return Response({
        'heating': reverse('heating:api-root', request=request, format=fmt),
    })


api_patterns = [
    url(r'^$', api_root),
    url(r'^heating/', include('heating.urls')),
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(api_patterns)),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'__debug__/', include(debug_toolbar.urls))
    ]
