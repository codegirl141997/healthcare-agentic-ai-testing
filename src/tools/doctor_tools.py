
from src.services.mock_hospital_api import MockHospitalAPI


def search_doctors_tool(hospital, specialty):
    """Search for doctors by specialty."""

    if not isinstance(specialty, str) or not specialty.strip():
        return {
            "status": "error",
            "reason": "invalid_specialty",
        }

    try:
        doctors = hospital.search_doctors(specialty)

        return {
            "status": "success",
            "doctors": doctors,
        }

    except Exception:
        return {
            "status": "error",
            "reason": "doctor_search_failed",
        }
