import pytest
from app.validators import validate_patient

VALID = dict(full_name="Jane Smith", phone="0712345678",
             date_of_birth="1990-02-15", reason="Skin rash", email="jane@example.com")


def check(**changes):
    """Valid details, with some fields changed for the test."""
    return validate_patient(**{**VALID, **changes})


def test_valid_details_pass():
    result = check()
    assert result["ok"] is True
    assert result["errors"] == {}


@pytest.mark.parametrize("field, bad_value", [
    ("full_name", "J"),                    # fewer than 2 letters
    ("full_name", "Jane123"),              # digits not allowed
    ("full_name", ""),                     # empty
    ("phone", "12345"),                    # too short
    ("phone", "07123abc78"),               # letters
    ("phone", "+1234567890123456"),        # 16 digits, too long
    ("email", "jane@"),                    # not a valid email
    ("date_of_birth", "1990-02-30"),       # date does not exist (spec example)
    ("date_of_birth", "15-02-1990"),       # wrong format
    ("date_of_birth", "2999-01-01"),       # in the future
    ("date_of_birth", "1890-01-01"),       # age over 120
    ("reason", ""),                        # empty
    ("reason", "x" * 201),                 # too long
])
def test_invalid_field_is_reported(field, bad_value):
    result = check(**{field: bad_value})
    assert result["ok"] is False
    assert field in result["errors"]       # the RIGHT field is reported


@pytest.mark.parametrize("phone", ["+94712345678", "071 234 5678", "071-234-5678"])
def test_common_phone_formats_are_accepted(phone):
    assert check(phone=phone)["ok"] is True


def test_email_is_optional():
    assert check(email=None)["ok"] is True
    assert check(email="")["ok"] is True


def test_values_are_cleaned():
    result = check(full_name="  Jane   Smith ", phone="071 234 5678", email="Jane@Example.com")
    assert result["cleaned"]["full_name"] == "Jane Smith"
    assert result["cleaned"]["phone"] == "0712345678"
    assert result["cleaned"]["email"] == "jane@example.com"