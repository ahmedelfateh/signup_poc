import pytest

from signup_form.calculators import FormScoreCalculator


@pytest.mark.django_db
class TestFormScoreCalculator:
    """Test cases for the FormScoreCalculator"""

    def test_simple_score_calculation(self):
        """Test score calculation for a simple schema with scores"""
        schema = {
            "properties": {
                "country": {
                    "type": "string",
                    "enum": ["US", "UK", "DE"],
                    "score": [{"US": 10}, {"UK": 5}, {"DE": 2}],
                }
            }
        }
        data = {"country": "US"}

        score = FormScoreCalculator.calculate_score(data, schema)
        assert score == 10

    def test_nested_object_score_calculation(self):
        """Test score calculation for nested objects"""
        schema = {
            "properties": {
                "preferences": {
                    "type": "object",
                    "properties": {
                        "color": {
                            "type": "string",
                            "enum": ["red", "blue", "green"],
                            "score": [{"red": 3}, {"blue": 5}, {"green": 2}],
                        }
                    },
                }
            }
        }
        data = {"preferences": {"color": "blue"}}

        score = FormScoreCalculator.calculate_score(data, schema)
        assert score == 5

    def test_multiple_fields_score_calculation(self):
        """Test score calculation with multiple fields"""
        schema = {
            "properties": {
                "age": {
                    "type": "integer",
                    "enum": [18, 25, 35],
                    "score": [{18: 1}, {25: 2}, {35: 3}],
                },
                "education": {
                    "type": "string",
                    "enum": ["high_school", "college", "graduate"],
                    "score": [{"high_school": 1}, {"college": 3}, {"graduate": 5}],
                },
            }
        }
        data = {"age": 25, "education": "graduate"}

        score = FormScoreCalculator.calculate_score(data, schema)
        assert score == 7  # 2 + 5 = 7

    def test_missing_field_score_calculation(self):
        """Test score calculation when fields are missing"""
        schema = {
            "properties": {
                "country": {
                    "type": "string",
                    "enum": ["US", "UK", "DE"],
                    "score": [{"US": 10}, {"UK": 5}, {"DE": 2}],
                }
            }
        }
        data = {"some_other_field": "value"}

        score = FormScoreCalculator.calculate_score(data, schema)
        assert score == 0  # No matching field, so score is 0

    def test_nationality_score_calculation(self):
        """Test score calculation with the nationality field from the example schema"""
        schema = {
            "properties": {
                "nationality": {
                    "type": "string",
                    "enum": ["DE", "IT", "JP", "US", "RU", "Other"],
                    "score": [
                        {"DE": 1},
                        {"IT": 0},
                        {"JP": 1},
                        {"US": 1},
                        {"RU": 1},
                        {"Other": 1},
                    ],
                    "scoure_type": "normal",
                }
            }
        }

        # Test with different nationality values
        data_de = {"nationality": "DE"}
        score_de = FormScoreCalculator.calculate_score(data_de, schema)
        assert score_de == 1

        data_it = {"nationality": "IT"}
        score_it = FormScoreCalculator.calculate_score(data_it, schema)
        assert score_it == 0
