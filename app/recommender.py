from app.validation import validate_profile


def clean(value):
    return str(value).strip().lower()


def clean_set(values):
    return {clean(value) for value in values}


def eligibility_failures(profile, item):
    failures = []
    if not item["active"]:
        failures.append("the item is inactive")
    if not (item["min_age"] <= profile["age"] <= item["max_age"]):
        failures.append(f"age must be between {item['min_age']} and {item['max_age']}")
    if clean(profile["education_level"]) not in clean_set(item["education_levels"]):
        failures.append("education level is not eligible")

    profile_city = clean(profile["city"])
    city_match = profile_city in clean_set(item["cities"])
    if not city_match and not item["remote_allowed"]:
        failures.append("city does not match and remote participation is not allowed")
    if clean(profile["mode_preference"]) == "remote" and not item["remote_allowed"]:
        failures.append("profile prefers remote but the item is onsite only")

    profile_skills = clean_set(profile["skills"])
    missing_skills = sorted(clean_set(item["required_skills"]) - profile_skills)
    if missing_skills:
        failures.append("missing required skills: " + ", ".join(missing_skills))
    if profile["experience_months"] < item["min_experience_months"]:
        failures.append(f"requires at least {item['min_experience_months']} months of experience")
    if profile["budget_inr"] < item["fee_inr"]:
        failures.append(f"budget must cover the INR {item['fee_inr']} fee")
    if profile["weekly_hours"] < item["min_weekly_hours"]:
        failures.append(f"requires at least {item['min_weekly_hours']} hours per week")
    if item["requires_laptop"] and not profile["has_laptop"]:
        failures.append("requires access to a laptop")
    if profile["available_start_days"] > item["starts_within_days"]:
        failures.append(f"user must be able to start within {item['starts_within_days']} days")
    return failures


def score_item(profile, item):
    profile_skills = clean_set(profile["skills"])
    profile_interests = clean_set(profile["interests"])
    preferred_overlap = clean_set(item["preferred_skills"]) & profile_skills
    interest_overlap = clean_set(item["interests"]) & profile_interests
    city_match = clean(profile["city"]) in clean_set(item["cities"])
    mode = clean(profile["mode_preference"])

    score = 50
    score += 9 * len(preferred_overlap)
    score += 11 * len(interest_overlap)
    score += 8 if city_match else 3 if item["remote_allowed"] else 0
    score += 6 if mode == "any" else 6 if mode in {"hybrid", "remote"} and item["remote_allowed"] else 3
    score += min(10, max(0, profile["experience_months"] - item["min_experience_months"]) // 2)
    score += min(8, max(0, profile["weekly_hours"] - item["min_weekly_hours"]) // 2)
    score += min(6, max(0, profile["budget_inr"] - item["fee_inr"]) // 2500)
    score -= max(0, item["starts_within_days"] - profile["available_start_days"]) // 14

    signals = []
    if interest_overlap:
        signals.append("interest fit on " + ", ".join(sorted(interest_overlap)))
    if preferred_overlap:
        signals.append("bonus skills in " + ", ".join(sorted(preferred_overlap)))
    if city_match:
        signals.append(f"local fit for {profile['city']}")
    elif item["remote_allowed"]:
        signals.append("remote eligibility")
    if profile["weekly_hours"] >= item["min_weekly_hours"] + 5:
        signals.append("healthy weekly availability")

    return score, signals


def reason_for(profile, item, rank, score, signals):
    signal_text = "; ".join(signals) if signals else "it clears every hard rule without a strong bonus signal"
    return (
        f"{item['name']} is ranked #{rank} with a score of {score} because the profile passes "
        f"the hard eligibility checks for age, education, location, required skills, budget, "
        f"availability, and equipment. The strongest match signals are {signal_text}. "
        f"It is a {item['category']} option that asks for {item['min_weekly_hours']} hours per week "
        f"and starts within {item['starts_within_days']} days."
    )


def recommend(profile, items, limit=3):
    errors = validate_profile(profile)
    if errors:
        return {"errors": errors, "recommendations": []}

    candidates = []
    rejected = []
    for item in items:
        failures = eligibility_failures(profile, item)
        if failures:
            rejected.append({"item_id": item["id"], "name": item["name"], "failures": failures})
            continue
        score, signals = score_item(profile, item)
        candidates.append({"item": item, "score": score, "signals": signals})

    candidates.sort(key=lambda candidate: (-candidate["score"], candidate["item"]["name"]))
    recommendations = []
    for index, candidate in enumerate(candidates[:limit], start=1):
        item = candidate["item"]
        recommendations.append(
            {
                "rank": index,
                "item_id": item["id"],
                "name": item["name"],
                "score": candidate["score"],
                "reason": reason_for(profile, item, index, candidate["score"], candidate["signals"]),
            }
        )

    response = {"recommendations": recommendations}
    if not recommendations:
        response["message"] = "No catalogue items matched the hard eligibility rules for this profile."
        response["rejected"] = rejected
    return response


def explain_item(item):
    mode = "remote or onsite" if item["remote_allowed"] else "onsite only"
    laptop = "must have a laptop" if item["requires_laptop"] else "does not need a laptop"
    return (
        f"{item['name']} is available to {', '.join(item['education_levels'])} learners aged "
        f"{item['min_age']} to {item['max_age']}. The user must be in {', '.join(item['cities'])} "
        f"or satisfy the {mode} rule, know {', '.join(item['required_skills']) or 'no mandatory skills'}, "
        f"have at least {item['min_experience_months']} months of experience, afford the INR "
        f"{item['fee_inr']} fee, commit {item['min_weekly_hours']} hours per week, and be able to "
        f"start within {item['starts_within_days']} days. The user {laptop}."
    )
