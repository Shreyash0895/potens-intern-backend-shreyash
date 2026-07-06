REQUIRED_PROFILE_FIELDS = {
    "age": int,
    "education_level": str,
    "city": str,
    "skills": list,
    "experience_months": int,
    "weekly_hours": int,
    "budget_inr": int,
    "interests": list,
    "has_laptop": bool,
    "available_start_days": int,
    "mode_preference": str,
}

REQUIRED_ITEM_FIELDS = {
    "id": str,
    "name": str,
    "category": str,
    "description": str,
    "min_age": int,
    "max_age": int,
    "education_levels": list,
    "cities": list,
    "remote_allowed": bool,
    "required_skills": list,
    "preferred_skills": list,
    "min_experience_months": int,
    "fee_inr": int,
    "min_weekly_hours": int,
    "interests": list,
    "requires_laptop": bool,
    "starts_within_days": int,
    "active": bool,
}


def validate_shape(payload, schema):
    missing = [field for field in schema if field not in payload]
    if missing:
        return [f"Missing required field: {field}" for field in missing]

    errors = []
    for field, expected_type in schema.items():
        value = payload.get(field)
        if expected_type is int and (not isinstance(value, int) or isinstance(value, bool)):
            errors.append(f"{field} must be an integer")
        elif expected_type is bool and not isinstance(value, bool):
            errors.append(f"{field} must be a boolean")
        elif expected_type is str and not isinstance(value, str):
            errors.append(f"{field} must be a string")
        elif expected_type is list and not isinstance(value, list):
            errors.append(f"{field} must be a list")
    return errors


def validate_profile(profile):
    errors = validate_shape(profile, REQUIRED_PROFILE_FIELDS)
    if errors:
        return errors

    if profile["age"] < 13:
        errors.append("age must be at least 13")
    if profile["experience_months"] < 0:
        errors.append("experience_months cannot be negative")
    if profile["weekly_hours"] < 0:
        errors.append("weekly_hours cannot be negative")
    if profile["budget_inr"] < 0:
        errors.append("budget_inr cannot be negative")
    if profile["available_start_days"] < 0:
        errors.append("available_start_days cannot be negative")
    if not all(isinstance(skill, str) for skill in profile["skills"]):
        errors.append("skills must contain only strings")
    if not all(isinstance(interest, str) for interest in profile["interests"]):
        errors.append("interests must contain only strings")
    if profile["mode_preference"] not in {"onsite", "remote", "hybrid", "any"}:
        errors.append("mode_preference must be onsite, remote, hybrid, or any")
    return errors


def validate_item(item):
    errors = validate_shape(item, REQUIRED_ITEM_FIELDS)
    if errors:
        return errors

    if item["min_age"] > item["max_age"]:
        errors.append("min_age cannot be greater than max_age")
    if item["fee_inr"] < 0:
        errors.append("fee_inr cannot be negative")
    if item["min_experience_months"] < 0:
        errors.append("min_experience_months cannot be negative")
    if item["min_weekly_hours"] < 0:
        errors.append("min_weekly_hours cannot be negative")
    for field in ("education_levels", "cities", "required_skills", "preferred_skills", "interests"):
        if not all(isinstance(value, str) for value in item[field]):
            errors.append(f"{field} must contain only strings")
    return errors
