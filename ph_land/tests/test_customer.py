import pytest

from app.domain.customer import Customer
from app.domain.models import UTCTZ


def test_customer_has_created_at_default():
    customer = Customer(first_name="Alice", last_name="Smith", email="alice@example.com")

    assert customer.created_at.tzinfo == UTCTZ


def test_blank_optional_contact_fields_are_treated_as_missing():
    customer = Customer(first_name="Alice", last_name="Smith", email="", phone="+1234567890")

    assert customer.email is None
    assert customer.phone == "+1234567890"


def test_email_must_contain_at_symbol():
    with pytest.raises(ValueError, match="@"):
        Customer(first_name="Alice", last_name="Smith", email="invalid-email")


def test_customer_may_have_both_phone_and_email():
    customer = Customer(first_name="Alice", last_name="Smith", email="alice@example.com", phone="123456")

    assert customer.email == "alice@example.com"
    assert customer.phone == "123456"
