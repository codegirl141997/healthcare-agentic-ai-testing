
from datetime import date, timedelta

import pytest

from src.tools.appointment_tools import check_availability_tool
from src.tools.booking_tools import book_appointment_tool


class FakeHospital:
    """Fake hospital service for isolated unit tests."""

    def __init__(self):
        self.slots = ["10:00", "11:00"]
        self.booking_result = {"status": "success", "booking_id": "B001"}
        self.availability_error = None
        self.booking_error = None
        self.availability_calls = 0
        self.booking_calls = 0

    def check_availability(self, doctor_id, appointment_date):
        self.availability_calls += 1

        if self.availability_error:
            raise self.availability_error

        return self.slots

    def book_appointment(
        self,
        doctor_id,
        appointment_date,
        appointment_time,
        confirmed,
    ):
        self.booking_calls += 1

        if self.booking_error:
            raise self.booking_error

        return self.booking_result


@pytest.fixture
def hospital():
    return FakeHospital()


# ---------------- Availability tool tests ----------------

def test_availability_returns_slots(hospital):
    result = check_availability_tool(
        hospital, "DOC001", date.today().isoformat()
    )

    assert result == {
        "status": "success",
        "slots": ["10:00", "11:00"],
    }


@pytest.mark.parametrize("doctor_id", ["", "   ", None, 123])
def test_availability_rejects_invalid_doctor_id(hospital, doctor_id):
    result = check_availability_tool(
        hospital, doctor_id, date.today().isoformat()
    )

    assert result == {
        "status": "error",
        "reason": "invalid_doctor_id",
    }
    assert hospital.availability_calls == 0


def test_availability_rejects_past_date(hospital):
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    result = check_availability_tool(hospital, "DOC001", yesterday)

    assert result == {"status": "error", "reason": "past_date"}
    assert hospital.availability_calls == 0


@pytest.mark.parametrize("appointment_date", ["not-a-date", "", None])
def test_availability_rejects_invalid_date(hospital, appointment_date):
    result = check_availability_tool(
        hospital, "DOC001", appointment_date
    )

    assert result == {"status": "error", "reason": "invalid_date"}
    assert hospital.availability_calls == 0


def test_availability_handles_service_failure(hospital):
    hospital.availability_error = RuntimeError("Service unavailable")

    result = check_availability_tool(
        hospital, "DOC001", date.today().isoformat()
    )

    assert result == {
        "status": "error",
        "reason": "availability_check_failed",
    }


# ---------------- Booking tool tests ----------------

def test_booking_succeeds_with_explicit_confirmation(hospital):
    result = book_appointment_tool(
        hospital,
        "DOC001",
        date.today().isoformat(),
        "10:00",
        confirmed=True,
    )

    assert result == {
        "status": "success",
        "booking_id": "B001",
    }
    assert hospital.booking_calls == 1


@pytest.mark.parametrize("confirmed", [False, None, "true", 1])
def test_booking_rejects_without_boolean_confirmation(
    hospital, confirmed
):
    result = book_appointment_tool(
        hospital,
        "DOC001",
        date.today().isoformat(),
        "10:00",
        confirmed=confirmed,
    )

    assert result == {
        "status": "rejected",
        "reason": "user_confirmation_required",
    }
    assert hospital.booking_calls == 0


def test_booking_handles_service_failure(hospital):
    hospital.booking_error = RuntimeError("Booking service unavailable")

    result = book_appointment_tool(
        hospital,
        "DOC001",
        date.today().isoformat(),
        "10:00",
        confirmed=True,
    )

    assert result == {
        "status": "error",
        "reason": "booking_service_failed",
    }
    assert hospital.booking_calls == 1
