import pytest

from signup_form.calculators import FormScoreCalculator, ScoreCalculatorFactory


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

    def test_weighted_score_calculation(self):
        """Test score calculation using the weighted score calculator"""
        schema = {
            "properties": {
                "risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "score": [
                        {"low": 5, "weight": 0.5},
                        {"medium": 10, "weight": 0.8},
                        {"high": 15, "weight": 1.2},
                    ],
                    "score_type": "weighted",
                }
            }
        }
        data = {"risk_level": "high"}

        score = FormScoreCalculator.calculate_score(data, schema)
        assert score == 18  # 15 * 1.2 = 18

    def test_calculator_factory(self):
        """Test the ScoreCalculatorFactory returns correct calculator types"""
        normal_calculator = ScoreCalculatorFactory.get_calculator("normal")
        weighted_calculator = ScoreCalculatorFactory.get_calculator("weighted")
        default_calculator = ScoreCalculatorFactory.get_calculator("nonexistent")

        # Test normal calculator
        score_list = [{"option1": 5}, {"option2": 10}]
        assert normal_calculator.calculate_field_score("option1", score_list) == 5
        assert normal_calculator.calculate_field_score("option2", score_list) == 10

        # Test weighted calculator with a weight
        weighted_score_list = [{"option1": 5, "weight": 2.0}]
        assert (
            weighted_calculator.calculate_field_score("option1", weighted_score_list)
            == 10.0
        )

        # Test that default calculator is returned for unknown types
        assert default_calculator.calculate_field_score("option1", score_list) == 5

    def test_mixed_calculator_types(self):
        """Test form with multiple fields using different calculator types"""
        schema = {
            "properties": {
                "standard_field": {
                    "type": "string",
                    "enum": ["A", "B", "C"],
                    "score": [{"A": 1}, {"B": 2}, {"C": 3}],
                    "score_type": "normal",
                },
                "weighted_field": {
                    "type": "string",
                    "enum": ["X", "Y", "Z"],
                    "score": [
                        {"X": 10, "weight": 0.5},
                        {"Y": 20, "weight": 1.0},
                        {"Z": 30, "weight": 1.5},
                    ],
                    "score_type": "weighted",
                },
            }
        }
        data = {"standard_field": "B", "weighted_field": "Z"}

        score = FormScoreCalculator.calculate_score(data, schema)
        assert score == 47  # 2 + (30 * 1.5) = 47
