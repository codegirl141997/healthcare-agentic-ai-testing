
import pytest

from src.services.mock_hospital_api import MockHospitalAPI


@pytest.fixture
def hospital():
    return MockHospitalAPI()


def test_search_doctors_by_specialty(hospital):
    doctors = hospital.search_doctors("cardiology")

    assert len(doctors) == 1
    assert doctors[0]["doctor_id"] == "DOC101"


def test_search_is_case_insensitive(hospital):
    doctors = hospital.search_doctors("CARDIOLOGY")

    assert len(doctors) == 1


def test_check_available_slots(hospital):
    slots = hospital.check_availability(
        "DOC101", "2026-10-19"
    )

    assert len(slots) == 2
    assert all(slot["available"] for slot in slots)


def test_booking_without_confirmation_is_rejected(hospital):
    result = hospital.book_appointment(
        "DOC101", "2026-10-19", "11:00"
    )

    assert result["status"] == "rejected"
    assert result["reason"] == "user_confirmation_required"

    slots = hospital.check_availability(
        "DOC101", "2026-10-19"
    )
    assert len(slots) == 2


def test_confirmed_booking_succeeds(hospital):
    result = hospital.book_appointment(
        "DOC101",
        "2026-10-19",
        "11:00",
        confirmed=True,
    )

    assert result["status"] == "confirmed"
    assert result["booking_id"].startswith("APT-")


def test_same_slot_cannot_be_booked_twice(hospital):
    first = hospital.book_appointment(
        "DOC101", "2026-10-19", "11:00",
        confirmed=True,
    )

    second = hospital.book_appointment(
        "DOC101", "2026-10-19", "11:00",
        confirmed=True,
    )

    assert first["status"] == "confirmed"
    assert second["status"] == "rejected"
    assert second["reason"] == "slot_unavailable"


def test_unknown_doctor_is_rejected(hospital):
    result = hospital.book_appointment(
        "DOC999", "2026-10-19", "11:00",
        confirmed=True,
    )

    assert result["status"] == "rejected"
    assert result["reason"] == "doctor_not_found"


def test_past_date_is_rejected(hospital):
    result = hospital.book_appointment(
        "DOC101", "2020-01-01", "11:00",
        confirmed=True,
    )

    assert result["status"] == "rejected"
    assert result["reason"] == "past_date"
