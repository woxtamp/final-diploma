import pytest
from rest_framework.test import APIClient
from model_bakery import baker


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def empty_payload():
    return {}


@pytest.fixture
def error_not_all_fields_completed():
    return 'Input Error! All required fields are not filled.'


@pytest.fixture
def register_correct_payload():
    return {
        "email": "test@test.com",
        "password": "Test1234_4321",
        "first_name": "Test",
        "last_name": "Test",
        "company": "Test",
        "position": "Test",
        "contacts": "Test"
    }


@pytest.fixture
def register_short_password():
    return {
        "email": "test@test.com",
        "password": "T_1",
        "first_name": "Test",
        "last_name": "Test",
        "company": "Test",
        "position": "Test",
        "contacts": "Test"
    }


@pytest.fixture
def register_incorrect_password():
    return {
        "email": "test@test.com",
        "password": "12345qwerty",
        "first_name": "Test",
        "last_name": "Test",
        "company": "Test",
        "position": "Test",
        "contacts": "Test"
    }


@pytest.fixture
def register_incorrect_email_payload():
    return {
        "email": "test",
        "password": "Test1234_4321",
        "first_name": "Test",
        "last_name": "Test",
        "company": "Test",
        "position": "Test",
        "contacts": "Test"
    }


@pytest.fixture
def login_correct_payload():
    return {
        "email": "test@test.com",
        "password": "Test1234_4321"
    }


@pytest.fixture
def login_incorrect_password_payload():
    return {
        "email": "test@test.com",
        "password": "Testt1234_4321"
    }