import unittest

from app.recommender import eligibility_failures, recommend
from seed_data import ITEMS


VALID_PROFILE = {
    "age": 21,
    "education_level": "undergraduate",
    "city": "Pune",
    "skills": ["python", "javascript", "html", "css", "excel", "linux", "documentation"],
    "experience_months": 8,
    "weekly_hours": 16,
    "budget_inr": 5000,
    "interests": ["machine learning", "apis", "data", "ui"],
    "has_laptop": True,
    "available_start_days": 3,
    "mode_preference": "hybrid",
}


class RecommenderTests(unittest.TestCase):
    def test_returns_top_three_ranked_matches(self):
        result = recommend(VALID_PROFILE, ITEMS)
        self.assertEqual(len(result["recommendations"]), 3)
        self.assertEqual([item["rank"] for item in result["recommendations"]], [1, 2, 3])
        self.assertGreaterEqual(result["recommendations"][0]["score"], result["recommendations"][1]["score"])

    def test_missing_required_profile_field_is_reported(self):
        profile = dict(VALID_PROFILE)
        del profile["budget_inr"]
        result = recommend(profile, ITEMS)
        self.assertIn("Missing required field: budget_inr", result["errors"])
        self.assertEqual(result["recommendations"], [])

    def test_boundary_age_is_eligible_when_equal_to_minimum(self):
        item = next(item for item in ITEMS if item["id"] == "mobile-web-starter")
        profile = dict(VALID_PROFILE, age=item["min_age"], skills=["html", "css"], education_level="school")
        failures = eligibility_failures(profile, item)
        self.assertNotIn("age must be between 16 and 25", failures)

    def test_no_match_returns_clear_message_and_rejections(self):
        profile = dict(
            VALID_PROFILE,
            age=14,
            skills=[],
            budget_inr=0,
            weekly_hours=1,
            has_laptop=False,
            education_level="school",
            city="Latur",
            mode_preference="remote",
        )
        result = recommend(profile, ITEMS)
        self.assertEqual(result["recommendations"], [])
        self.assertIn("No catalogue items matched", result["message"])
        self.assertGreater(len(result["rejected"]), 0)

    def test_required_skill_failure_is_explained(self):
        item = next(item for item in ITEMS if item["id"] == "computer-vision-mini-lab")
        profile = dict(VALID_PROFILE, skills=["python"])
        failures = eligibility_failures(profile, item)
        self.assertIn("missing required skills: numpy", failures)


if __name__ == "__main__":
    unittest.main()
