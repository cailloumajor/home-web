from rest_framework import status
from rest_framework.test import APIClient


def test_api_root():
    client = APIClient()
    assert client.get('/api/').status_code == status.HTTP_200_OK
