"""
Tool schemas: what the LLM sees about each tool.
The LLM decides WHEN to call a tool by reading the "description".
Write descriptions like instructions to a new employee.
"""

def _tool(name: str, description: str, properties: dict, required: list) -> dict:
    """Small helper so each schema is short and consistent."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


TOOL_SCHEMAS = [
    _tool(
        "get_hospital_info",
        "Get hospital details: name, address, phone, email, emergency number, opening and "
        "visiting hours, departments, facilities, what to bring and payment methods. "
        "Use for ANY question about the hospital itself.",
        {}, [],
    ),
    _tool(
        "list_doctors",
        "List doctors with their speciality, fee and working days. Optionally filter by "
        "speciality (e.g. 'cardiology'). Use this to find a doctor_id before checking slots.",
        {"speciality": {"type": "string", "description": "Optional. e.g. cardiology, dermatology"}},
        [],
    ),
    _tool(
        "get_doctor_details",
        "Get one doctor's full details: fee, room, floor and working days.",
        {"doctor_id": {"type": "integer", "description": "doctor_id from list_doctors"}},
        ["doctor_id"],
    ),
    _tool(
        "get_available_slots",
        "Get FREE future appointment times for one doctor. Always use this before offering "
        "any time. Never offer a time that this tool did not return.",
        {
            "doctor_id": {"type": "integer", "description": "doctor_id from list_doctors"},
            "slot_date": {"type": "string", "description": "Optional. Date in YYYY-MM-DD format"},
        },
        ["doctor_id"],
    ),
    _tool(
        "validate_patient_details",
        "Check the patient's details before booking. Call this as soon as you have the name, "
        "phone, date of birth and reason. If field_errors are returned, ask the patient to "
        "correct only those fields.",
        {
            "full_name": {"type": "string"},
            "phone": {"type": "string"},
            "date_of_birth": {"type": "string", "description": "YYYY-MM-DD"},
            "reason": {"type": "string", "description": "Short reason for the visit"},
            "email": {"type": "string", "description": "Optional"},
        },
        ["full_name", "phone", "date_of_birth", "reason"],
    ),
    _tool(
        "prepare_booking",
        "Prepare a booking for a chosen slot with VALID patient details. This does NOT book. "
        "It returns a summary and a booking_ref. After calling it, read the summary to the "
        "patient and ask if they want to confirm.",
        {
            "slot_id": {"type": "integer", "description": "slot_id from get_available_slots"},
            "full_name": {"type": "string"},
            "phone": {"type": "string"},
            "date_of_birth": {"type": "string", "description": "YYYY-MM-DD"},
            "reason": {"type": "string"},
            "email": {"type": "string", "description": "Optional"},
        },
        ["slot_id", "full_name", "phone", "date_of_birth", "reason"],
    ),
    _tool(
        "confirm_booking",
        "Book the appointment for real. Call ONLY after the patient has clearly said yes to "
        "the summary from prepare_booking, in their latest message.",
        {"booking_ref": {"type": "string", "description": "booking_ref from prepare_booking"}},
        ["booking_ref"],
    ),
]