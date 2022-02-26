import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_403_FORBIDDEN
from django.conf import settings


# успешное добавление контакта
@pytest.mark.django_db
def test_user_contact_create_correct(api_client, register_correct_payload, login_correct_payload,
                                     contact_create_correct):
    api_client.post(reverse('backend:user-register'), register_correct_payload)
    token = api_client.post(reverse('backend:user-login'), login_correct_payload).json()['Token']

    url_contact = reverse('backend:user-contact')
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    response = api_client.post(url_contact, contact_create_correct)

    assert response.status_code == HTTP_201_CREATED

    response_json = response.json()
    assert len(response_json) == 8
    assert response_json['id'] == 1
    assert response_json['house'] == contact_create_correct['house']
    assert response_json['city'] == contact_create_correct['city']
    assert response_json['street'] == contact_create_correct['street']
    assert response_json['structure'] == ''
    assert response_json['building'] == ''
    assert response_json['apartment'] == ''


# неуспешное добавление контакта превышающее лимит
@pytest.mark.django_db
def test_user_contact_create_extra_limit(api_client, register_correct_payload, login_correct_payload,
                                         contact_create_correct):
    settings._wrapped.LIMIT_CONTACTS = 1

    api_client.post(reverse('backend:user-register'), register_correct_payload)
    token = api_client.post(reverse('backend:user-login'), login_correct_payload).json()['Token']

    url_contact = reverse('backend:user-contact')
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    api_client.post(url_contact, contact_create_correct)
    response = api_client.post(url_contact, contact_create_correct)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Errors']['non_field_errors'][0] == 'Contacts cannot be more than  1'


# неуспешное добавление контакта при отсутствии авторизации
@pytest.mark.django_db
def test_user_contact_create_non_authorized(api_client, contact_create_correct, error_not_authorized):
    url_contact = reverse('backend:user-contact')
    response = api_client.post(url_contact, contact_create_correct)

    assert response.status_code == HTTP_403_FORBIDDEN

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Error'] == error_not_authorized


# неуспешное добавление контакта из-за отсутствия обязательных полей
@pytest.mark.django_db
def test_user_contact_create_unavailable(api_client, register_correct_payload, login_correct_payload,
                                         empty_payload, error_not_all_fields_completed):
    api_client.post(reverse('backend:user-register'), register_correct_payload)
    token = api_client.post(reverse('backend:user-login'), login_correct_payload).json()['Token']

    url_contact = reverse('backend:user-contact')
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    response = api_client.post(url_contact, empty_payload)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Errors'] == error_not_all_fields_completed


# успешное редактирование контакта
@pytest.mark.django_db
def test_user_contact_edit_correct(api_client, register_correct_payload, login_correct_payload,
                                   contact_create_correct, contact_edit_correct):
    api_client.post(reverse('backend:user-register'), register_correct_payload)
    token = api_client.post(reverse('backend:user-login'), login_correct_payload).json()['Token']

    url_contact = reverse('backend:user-contact')
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    api_client.post(url_contact, contact_create_correct)
    response = api_client.put(url_contact, contact_edit_correct)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()

    assert len(response_json) == 8
    assert response_json['id'] == 1
    assert response_json['house'] == contact_edit_correct['house']
    assert response_json['city'] == contact_edit_correct['city']
    assert response_json['street'] == contact_edit_correct['street']
    assert response_json['structure'] == contact_edit_correct['structure']
    assert response_json['building'] == contact_edit_correct['building']
    assert response_json['apartment'] == contact_edit_correct['apartment']


# неуспешное редактирование контакта из-за отсутствия обязательных полей
@pytest.mark.django_db
def test_user_contact_edit_unavailable(api_client, register_correct_payload, login_correct_payload,
                                       contact_create_correct, empty_payload, error_not_all_fields_completed):
    api_client.post(reverse('backend:user-register'), register_correct_payload)
    token = api_client.post(reverse('backend:user-login'), login_correct_payload).json()['Token']

    url_contact = reverse('backend:user-contact')
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    api_client.post(url_contact, contact_create_correct)
    response = api_client.put(url_contact, empty_payload)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Errors'] == error_not_all_fields_completed


# неуспешное редактирование контакта из-за отсутствия авторизации
@pytest.mark.django_db
def test_user_contact_edit_unavailable(api_client, contact_edit_correct, error_not_authorized):
    url_contact = reverse('backend:user-contact')
    response = api_client.put(url_contact, contact_edit_correct)

    assert response.status_code == HTTP_403_FORBIDDEN

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Error'] == error_not_authorized


# успешное получение контакта из списка
@pytest.mark.django_db
def test_user_contact_get_list_correct(api_client, register_correct_payload, login_correct_payload,
                                       contact_create_correct):
    api_client.post(reverse('backend:user-register'), register_correct_payload)
    token = api_client.post(reverse('backend:user-login'), login_correct_payload).json()['Token']

    url_contact = reverse('backend:user-contact')
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    api_client.post(url_contact, contact_create_correct)
    response = api_client.get(url_contact)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]['id'] == 1
    assert response_json[0]['house'] == contact_create_correct['house']
    assert response_json[0]['city'] == contact_create_correct['city']
    assert response_json[0]['street'] == contact_create_correct['street']


# успешное получение пустого списка при отсутствии контактов
@pytest.mark.django_db
def test_user_contact_get_empty_list(api_client, register_correct_payload, login_correct_payload,
                                     contact_create_correct):
    api_client.post(reverse('backend:user-register'), register_correct_payload)
    token = api_client.post(reverse('backend:user-login'), login_correct_payload).json()['Token']

    url_contact = reverse('backend:user-contact')
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    response = api_client.get(url_contact)

    assert response.status_code == HTTP_200_OK

    response_json = response.json()

    assert response_json == []


# неуспешное получение списка контактов при отсутствии авторизации
@pytest.mark.django_db
def test_user_contact_get_not_authorized(api_client, error_not_authorized):
    url_contact = reverse('backend:user-contact')
    response = api_client.get(url_contact)

    assert response.status_code == HTTP_403_FORBIDDEN

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Error'] == error_not_authorized


# успешное удаление контакта
@pytest.mark.django_db
def test_user_contact_delete_correct(api_client, register_correct_payload, login_correct_payload,
                                     contact_create_correct):
    api_client.post(reverse('backend:user-register'), register_correct_payload)
    token = api_client.post(reverse('backend:user-login'), login_correct_payload).json()['Token']

    url_contact = reverse('backend:user-contact')
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    api_client.post(url_contact, contact_create_correct)

    response_delete = api_client.delete(url_contact, {"id": "1"})
    assert response_delete.status_code == HTTP_200_OK
    response_delete_json = response_delete.json()
    assert len(response_delete_json) == 1
    assert response_delete_json['Status'] is True

    response_get = api_client.get(url_contact)
    assert response_get.status_code == HTTP_200_OK
    response_get_json = response_get.json()
    assert response_get_json == []


# неуспешное получение списка контактов при отсутствии авторизации
@pytest.mark.django_db
def test_user_contact_delete_not_authorized(api_client, error_not_authorized):
    url_contact = reverse('backend:user-contact')
    response = api_client.delete(url_contact, {"id": "1"})

    assert response.status_code == HTTP_403_FORBIDDEN

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json['Status'] is False
    assert response_json['Error'] == error_not_authorized
