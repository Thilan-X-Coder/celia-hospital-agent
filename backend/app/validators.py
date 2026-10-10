"""
Patient detail validation (Spec Section 7).

Returns field-by-field errors so Celia can ask for ONE specific correction.
Also returns cleaned values (extra spaces removed, phone normalised).
"""
import re
from datetime import date

NAME_RE = re.compile(r"^[A-Za-z .\-]+$")          # letters, spaces, dots, hyphens
PHONE_RE = re.compile(r"^\+?\d{9,15}$")            # optional +, then 9-15 digits
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")   # exactly YYYY-MM-DD
MAX_AGE = 120
MAX_REASON = 200


def clean_phone(phone: str | None) -> str:
    """Remove spaces, dashes and brackets: '071 234-5678' -> '0712345678'."""
    return re.sub(r"[\s\-()]", "", phone or "")


def _age_on(dob: date, today: date) -> int:
    had_birthday = (today.month, today.day) >= (dob.month, dob.day)
    return today.year - dob.year - (0 if had_birthday else 1)


def validate_patient(full_name, phone, date_of_birth, reason, email=None) -> dict:
    errors: dict[str, str] = {}
    cleaned: dict[str, str | None] = {}

    # --- Full name ---
    name = " ".join((full_name or "").split())            # collapse extra spaces
    if sum(ch.isalpha() for ch in name) < 2:
        errors["full_name"] = "Please give a full name with at least 2 letters."
    elif not NAME_RE.match(name):
        errors["full_name"] = "A name can only have letters, spaces, dots and hyphens."
    else:
        cleaned["full_name"] = name

    # --- Phone ---
    phone_clean = clean_phone(phone)
    if not PHONE_RE.match(phone_clean):
        errors["phone"] = "The phone number must have 9 to 15 digits and may start with +."
    else:
        cleaned["phone"] = phone_clean

    # --- Email (optional) ---
    email_clean = (email or "").strip()
    if email_clean and not EMAIL_RE.match(email_clean):
        errors["email"] = "That email address does not look correct."
    else:
        cleaned["email"] = email_clean.lower() or None

    # --- Date of birth ---
    dob_text = (date_of_birth or "").strip()
    try:
        if not ISO_DATE_RE.match(dob_text):
            raise ValueError("wrong format")
        dob = date.fromisoformat(dob_text)                 # rejects 1990-02-30
        today = date.today()
        if dob > today:
            errors["date_of_birth"] = "The date of birth cannot be in the future."
        elif _age_on(dob, today) > MAX_AGE:
            errors["date_of_birth"] = "Please check the date of birth. The age cannot be over 120."
        else:
            cleaned["date_of_birth"] = dob_text
    except ValueError:
        errors["date_of_birth"] = "The date of birth must be a real date in YYYY-MM-DD format."

    # --- Reason for visit ---
    reason_clean = " ".join((reason or "").split())
    if not reason_clean:
        errors["reason"] = "Please tell me the reason for the visit."
    elif len(reason_clean) > MAX_REASON:
        errors["reason"] = f"Please keep the reason under {MAX_REASON} characters."
    else:
        cleaned["reason"] = reason_clean

    return {"ok": not errors, "errors": errors, "cleaned": cleaned}