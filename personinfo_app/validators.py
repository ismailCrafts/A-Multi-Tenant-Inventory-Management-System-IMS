import re


def validate_person_form(data):
    """
    Validates a person form (Supplier/Customer).
    Steps:
    1. Extract and normalize name and mobile from data.
    2. Ensure name is provided.
    3. Ensure mobile is provided.
    4. Validate mobile format (10–15 digits).
    5. Return (True, None) if valid, else (False, error message).
    """

    # Step 1: Extract and normalize fields
    name = data.get('name', '').strip()
    mobile = data.get('mobile', '').strip()

    # Step 2: Validate name presence
    if not name:
        return False, "Name is required."

    # Step 3: Validate mobile presence
    if not mobile:
        return False, "Mobile is required."

    # Step 4: Validate mobile format (10–15 digits only)
    if not re.fullmatch(r'\d{10,15}', mobile):
        return False, "Mobile number must be 10–15 digits."

    # Step 5: Valid → return success
    return True, None
