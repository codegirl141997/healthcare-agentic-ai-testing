
def book_appointment_tool(
    hospital,
    doctor_id,
    appointment_date,
    appointment_time,
    confirmed=False,
):
    """Request an appointment booking through the hospital service."""

    if confirmed is not True:
        return {
            "status": "rejected",
            "reason": "user_confirmation_required",
        }

    try:
        return hospital.book_appointment(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            confirmed=confirmed,
        )

    except Exception:
        return {
            "status": "error",
            "reason": "booking_service_failed",
        }
