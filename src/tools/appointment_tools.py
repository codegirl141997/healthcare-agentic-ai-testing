
from datetime import date


def check_availability_tool(hospital, doctor_id, appointment_date):
    """Check available appointment slots for a doctor."""

    if not isinstance(doctor_id, str) or not doctor_id.strip():
        return {
            "status": "error",
            "reason": "invalid_doctor_id",
        }

    try:
        requested_date = date.fromisoformat(appointment_date)

        if requested_date < date.today():
            return {
                "status": "error",
                "reason": "past_date",
            }

        slots = hospital.check_availability(
            doctor_id,
            appointment_date,
        )

        return {
            "status": "success",
            "slots": slots,
        }

    except (ValueError, TypeError):
        return {
            "status": "error",
            "reason": "invalid_date",
        }

    except Exception:
        return {
            "status": "error",
            "reason": "availability_check_failed",
        }
