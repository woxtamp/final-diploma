import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND, \
    HTTP_400_BAD_REQUEST


# успешная регистрация
@pytest.mark.django_db
def test_user_register_correct(api_client, register_correct_payload):
    url_register = reverse('backend:user-register')
    response = api_client.post(url_register, register_correct_payload)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 1
    assert response_json['Status'] is True


# ошибка регистрации при отсутствии обязательных полей в теле запроса
@pytest.mark.django_db
def test_user_register_unavailable(api_client, empty_payload, error_not_all_fields_completed):
    url_register = reverse('backend:user-register')
    response = api_client.post(url_register, empty_payload)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Errors'] == error_not_all_fields_completed


# ошибка регистрации при указании некоректного email
@pytest.mark.django_db
def test_user_register_incorrect_email(api_client, register_incorrect_email_payload):
    url_register = reverse('backend:user-register')
    response = api_client.post(url_register, register_incorrect_email_payload)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Errors']['email'][0] == "Enter a valid email address."


# ошибка регистрации при указании короткого пароля
@pytest.mark.django_db
def test_user_register_short_password(api_client, register_short_password):
    url_register = reverse('backend:user-register')
    response = api_client.post(url_register, register_short_password)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Errors']['password'][0] \
           == "This password is too short. It must contain at least 8 characters."


# ошибка регистрации при указании некорректного пароля
@pytest.mark.django_db
def test_user_register_incorrect_password(api_client, register_incorrect_password):
    url_register = reverse('backend:user-register')
    response = api_client.post(url_register, register_incorrect_password)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Errors']['password'][0] == "This password is too common."


# ошибка регистрации при указании уже зарегистрированного адреса почты
@pytest.mark.django_db
def test_user_register_correct(api_client, register_correct_payload):
    url_register = reverse('backend:user-register')
    api_client.post(url_register, register_correct_payload)
    response = api_client.post(url_register, register_correct_payload)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Errors']['email'][0] == "Пользователь with this email address already exists."
