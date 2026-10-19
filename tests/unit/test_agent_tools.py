
import pytest

from src.services.mock_hospital_api import MockHospitalAPI
from src.tools.doctor_tools import search_doctors_tool
from src.tools.appointment_tools import check_availability_tool
from src.tools.booking_tools import book_appointment_tool


@pytest.fixture
def hospital():
    return MockHospitalAPI()


def test_search_doctors_success(hospital):
    result = search_doctors_tool(hospital, "cardiology")

    assert result["status"] == "success"
    assert result["doctors"][0]["doctor_id"] == "DOC101"


def test_search_doctors_rejects_empty_specialty(hospital):
    result = search_doctors_tool(hospital, "  ")

    assert result["status"] == "error"
    assert result["reason"] == "invalid_specialty"


def test_check_availability_success(hospital):
    result = check_availability_tool(
        hospital, "DOC101", "2026-10-19"
    )

    assert result["status"] == "success"
    assert len(result["slots"]) == 2


def test_check_availability_rejects_invalid_date(hospital):
    result = check_availability_tool(
        hospital, "DOC101", "not-a-date"
    )

    assert result["status"] == "error"
    assert result["reason"] == "invalid_date"


def test_booking_requires_confirmation(hospital):
    result = book_appointment_tool(
        hospital,
        "DOC101",
        "2026-10-19",
        "11:00",
    )

    assert result["status"] == "rejected"
    assert result["reason"] == "user_confirmation_required"
    assert hospital.bookings == {}


def test_confirmed_booking_succeeds(hospital):
    result = book_appointment_tool(
        hospital,
        "DOC101",
        "2026-10-19",
        "11:00",
        confirmed=True,
    )

    assert result["status"] == "confirmed"
    assert result["booking_id"].startswith("APT-")
    assert len(hospital.bookings) == 1


def test_duplicate_booking_is_rejected(hospital):
    first = book_appointment_tool(
        hospital,
        "DOC101",
        "2026-10-19",
        "11:00",
        confirmed=True,
    )

    second = book_appointment_tool(
        hospital,
        "DOC101",
        "2026-10-19",
        "11:00",
        confirmed=True,
    )

    assert first["status"] == "confirmed"
    assert second["status"] == "rejected"
    assert second["reason"] == "slot_unavailable"
    assert len(hospital.bookings) == 1


def test_doctor_service_failure_is_handled(hospital, monkeypatch):
    def raise_error(specialty):
        raise RuntimeError("Simulated service failure")

    monkeypatch.setattr(hospital, "search_doctors", raise_error)

    result = search_doctors_tool(hospital, "cardiology")

    assert result["status"] == "error"
    assert result["reason"] == "doctor_search_failed"
