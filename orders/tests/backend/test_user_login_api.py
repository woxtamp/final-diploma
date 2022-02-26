import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK


# успешный логин
@pytest.mark.django_db
def test_user_login_correct(api_client, register_correct_payload, login_correct_payload):
    api_client.post(reverse('backend:user-register'), register_correct_payload)
    url_login = reverse('backend:user-login')

    response = api_client.post(url_login, login_correct_payload)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is True
    assert response_json['Token'] is not None


# неуспешный логин из-за неправильного пароля
@pytest.mark.django_db
def test_user_login_incorrect_password(api_client, register_correct_payload, login_incorrect_password_payload):
    api_client.post(reverse('backend:user-register'), register_correct_payload)
    url_login = reverse('backend:user-login')

    response = api_client.post(url_login, login_incorrect_password_payload)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Errors'] == 'Authorisation Error.'


# неуспешный логин под несуществующим пользователем
@pytest.mark.django_db
def test_user_login_not_exist(api_client, register_correct_payload, login_incorrect_password_payload):
    url_login = reverse('backend:user-login')

    response = api_client.post(url_login, login_incorrect_password_payload)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Errors'] == 'Authorisation Error.'
