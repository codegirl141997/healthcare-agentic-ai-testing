
from datetime import date
from uuid import uuid4


class MockHospitalAPI:
    """Simulated hospital appointment service."""

    def __init__(self):
        self.doctors = [
            {
                "doctor_id": "DOC101",
                "name": "Dr. Asha",
                "specialty": "cardiology",
            },
            {
                "doctor_id": "DOC102",
                "name": "Dr. Rahul",
                "specialty": "dermatology",
            },
        ]

        self.slots = [
            {
                "doctor_id": "DOC101",
                "date": "2026-10-19",
                "time": "11:00",
                "available": True,
            },
            {
                "doctor_id": "DOC101",
                "date": "2026-10-19",
                "time": "15:00",
                "available": True,
            },
            {
                "doctor_id": "DOC102",
                "date": "2026-10-19",
                "time": "10:00",
                "available": True,
            },
        ]

        self.bookings = {}

    def search_doctors(self, specialty):
        specialty = specialty.strip().lower()

        return [
            doctor.copy()
            for doctor in self.doctors
            if doctor["specialty"] == specialty
        ]

    def check_availability(self, doctor_id, appointment_date):
        return [
            slot.copy()
            for slot in self.slots
            if slot["doctor_id"] == doctor_id
            and slot["date"] == appointment_date
            and slot["available"]
        ]

    def book_appointment(
        self,
        doctor_id,
        appointment_date,
        appointment_time,
        confirmed=False,
    ):
        """Book only after explicit confirmation."""

        if confirmed is not True:
            return {
                "status": "rejected",
                "reason": "user_confirmation_required",
            }

        try:
            requested_date = date.fromisoformat(appointment_date)
        except (ValueError, TypeError):
            return {
                "status": "rejected",
                "reason": "invalid_date",
            }

        if requested_date < date.today():
            return {
                "status": "rejected",
                "reason": "past_date",
            }

        doctor_exists = any(
            doctor["doctor_id"] == doctor_id
            for doctor in self.doctors
        )

        if not doctor_exists:
            return {
                "status": "rejected",
                "reason": "doctor_not_found",
            }

        for slot in self.slots:
            if (
                slot["doctor_id"] == doctor_id
                and slot["date"] == appointment_date
                and slot["time"] == appointment_time
                and slot["available"]
            ):
                slot["available"] = False

                booking_id = f"APT-{uuid4().hex[:8].upper()}"

                booking = {
                    "booking_id": booking_id,
                    "doctor_id": doctor_id,
                    "date": appointment_date,
                    "time": appointment_time,
                    "status": "confirmed",
                }

                self.bookings[booking_id] = booking
                return booking.copy()

        return {
            "status": "rejected",
            "reason": "slot_unavailable",
        }
