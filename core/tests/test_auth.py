# -*- coding: utf-8 -*-
# pylint: disable=no-self-use

from django.contrib.auth import authenticate, get_user
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpRequest

import pytest


USERNAME = 'test_admin'
PASSWORD = 'test_password'


@pytest.fixture
def auth_settings(settings):
    settings.AUTHENTICATION_BACKENDS = [
        'core.auth.backends.SettingsBackend'
    ]
    settings.ADMIN_LOGIN = USERNAME
    settings.ADMIN_PASSWORD = make_password(PASSWORD)


@pytest.mark.django_db
@pytest.mark.usefixtures('auth_settings')
class TestSettingsBackend:

    def test_authenticate(self):
        bad_pass = make_password('bad_password')
        assert authenticate(username='bad_user', password=PASSWORD) is None
        assert authenticate(username=USERNAME, password=bad_pass) is None
        user = authenticate(username=USERNAME, password=PASSWORD)
        assert isinstance(user, User)
        assert user.username == USERNAME

    def test_get_user(self, client):
        client.login(username=USERNAME, password=PASSWORD)
        request = HttpRequest()
        request.session = client.session
        request.session['_auth_user_id'] = '-1'
        user = get_user(request)
        assert isinstance(user, AnonymousUser)
        request.session = client.session
        user = get_user(request)
        assert isinstance(user, User)
        assert user.username == USERNAME
