from abc import ABC, abstractmethod


class BaseScoreCalculator(ABC):
    """Abstract base class for score calculation strategies"""

    @abstractmethod
    def calculate_field_score(self, user_choice, score_list):
        """Calculate the score for a single field"""
        pass


class NormalScoreCalculator(BaseScoreCalculator):
    """Standard score calculator that finds exact matches in the score list"""

    def calculate_field_score(self, user_choice, score_list):
        for score_item in score_list:
            if user_choice in score_item:
                return score_item[user_choice]
        return 0


class WeightedScoreCalculator(BaseScoreCalculator):
    """Example of a weighted score calculator that applies weights to scores"""

    def calculate_field_score(self, user_choice, score_list):
        # Example implementation - replace with actual weighted scoring logic
        base_score = 0
        weight = 1.0

        for score_item in score_list:
            if user_choice in score_item:
                base_score = score_item[user_choice]
                # Get weight if specified in the score item
                weight = score_item.get("weight", 1.0)
                break

        return base_score * weight


class ScoreCalculatorFactory:
    """Factory class to create appropriate score calculator instances"""

    @staticmethod
    def get_calculator(score_type="normal"):
        """Return the appropriate calculator based on score_type"""
        calculators = {
            "normal": NormalScoreCalculator(),
            "weighted": WeightedScoreCalculator(),
            # Add more calculator types here as needed
        }

        # Return the requested calculator or default to normal
        return calculators.get(score_type, calculators["normal"])


class FormScoreCalculator:
    """
    Calculator for computing scores based on form responses
    compared to schema score definitions
    """

    @staticmethod
    def calculate_score(data, schema):
        """
        Calculate the total score for form responses
        based on the schema score definitions

        Args:
            data: Form response data
            schema: JSON schema with scoring information

        Returns:
            float: Total calculated score
        """
        total_score = 0.0

        # Get properties from schema
        properties = schema.get("properties", {})

        # Loop through all properties in the schema
        for field_name, field_def in properties.items():
            # If this field has a score definition and user answered it
            if "score" in field_def and field_name in data:
                user_choice = data[field_name]
                score_list = field_def.get("score", [])
                score_type = field_def.get("score_type", "normal")

                # Get the appropriate calculator based on score_type
                calculator = ScoreCalculatorFactory.get_calculator(score_type)
                score_value = calculator.calculate_field_score(
                    user_choice, score_list)

                # Add to total score
                total_score += score_value

            # Handle nested objects with scores
            elif field_def.get("type") == "object" and field_name in data:
                # Recursively calculate scores for nested object
                nested_data = data[field_name]
                nested_schema = {"properties": field_def.get("properties", {})}
                nested_score = FormScoreCalculator.calculate_score(
                    nested_data, nested_schema
                )
                total_score += nested_score

        return total_score
