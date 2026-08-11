from app.logging_config import scrub_event
from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_event_redacts_pii_in_nested_collections() -> None:
    event = {
        "payload": {
            "contacts": [
                "student@vinuni.edu.vn",
                {"phones": ("090 123 4567",)},
            ]
        }
    }

    scrubbed = scrub_event(None, "info", event)

    assert scrubbed["payload"]["contacts"][0] == "[REDACTED_EMAIL]"
    assert scrubbed["payload"]["contacts"][1]["phones"][0] == "[REDACTED_PHONE_VN]"
