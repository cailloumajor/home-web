# pylint: skip-file

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password


class SettingsBackend:
    """
    Authenticates against the settings ADMIN_LOGIN and ADMIN_PASSWORD
    Use the login name and a hash of the password.
    """

    def authenticate(self, username=None, password=None):
        UserModel = get_user_model()
        login_valid = (username == settings.ADMIN_LOGIN)
        pwd_valid = check_password(password, settings.ADMIN_PASSWORD)
        if login_valid and pwd_valid:
            try:
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                user = UserModel(username=username)
                user.is_staff = True
                user.is_superuser = True
                user.save()
            return user
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
