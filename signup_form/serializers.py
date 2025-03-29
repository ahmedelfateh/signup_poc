from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from jsonschema import ValidationError as JsonSchemaValidationError
from rest_framework import serializers

from .calculators import FormScoreCalculator
from .models import (
    FlowStep,
    FormFlow,
    FormResponse,
    FormSchema,
    UserJourney,
    WhiteLabel,
)
from .validators import FormValidator


class WhiteLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhiteLabel
        fields = ["id", "name", "slug", "is_active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class FormSchemaSerializer(serializers.ModelSerializer):
    white_label_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FormSchema
        fields = [
            "id",
            "title",
            "description",
            "schema",
            "ui_schema",
            "white_label",
            "white_label_name",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_white_label_name(self, obj):
        return obj.white_label.name if obj.white_label else None

    def validate_schema(self, value):
        """Validate that the schema is a valid JSON Schema"""
        try:
            # Basic validation that it's a valid schema format
            if not isinstance(value, dict):
                raise serializers.ValidationError("Schema must be a valid JSON object")

            # Check for required fields in a schema
            required_fields = ["type", "properties"]
            for field in required_fields:
                if field not in value:
                    raise serializers.ValidationError(
                        f"Schema must contain '{field}' field"
                    )

            return value
        except Exception as e:
            raise serializers.ValidationError(f"Invalid schema format: {str(e)}") from e

    def validate_ui_schema(self, value):
        """Validate that the UI schema is a valid JSON object"""
        if value is None:
            return value

        try:
            if not isinstance(value, dict):
                raise serializers.ValidationError(
                    "UI Schema must be a valid JSON object"
                )

            return value
        except Exception as e:
            raise serializers.ValidationError(
                f"Invalid UI schema format: {str(e)}"
            ) from e


class FlowStepSerializer(serializers.ModelSerializer):
    form_title = serializers.CharField(source="form_schema.title", read_only=True)

    class Meta:
        model = FlowStep
        fields = [
            "id",
            "flow",
            "form_schema",
            "form_title",
            "step_number",
            "is_required",
        ]


class FormFlowSerializer(serializers.ModelSerializer):
    steps = FlowStepSerializer(many=True, read_only=True)
    white_label_name = serializers.CharField(source="white_label.name", read_only=True)

    class Meta:
        model = FormFlow
        fields = [
            "id",
            "name",
            "description",
            "white_label",
            "white_label_name",
            "journey_type",
            "is_active",
            "created_at",
            "updated_at",
            "steps",
        ]
        read_only_fields = ["created_at", "updated_at"]


class UserJourneySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    flow_name = serializers.CharField(source="flow.name", read_only=True)
    current_step_number = serializers.IntegerField(
        source="current_step.step_number", read_only=True
    )
    previous_journey_id = serializers.IntegerField(
        source="previous_journey.id", read_only=True, allow_null=True
    )
    next_journey_ids = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,  # Make user field optional
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = UserJourney
        fields = [
            "id",
            "user",
            "user_email",
            "flow",
            "flow_name",
            "journey_type",
            "current_step",
            "current_step_number",
            "is_complete",
            "started_at",
            "completed_at",
            "previous_journey",
            "previous_journey_id",
            "is_upgrade_journey",
            "next_journey_ids",
        ]
        read_only_fields = ["started_at", "completed_at", "next_journey_ids"]

    def get_next_journey_ids(self, obj):
        """Get IDs of any next journeys in an upgrade sequence"""
        return list(obj.next_journey.values_list("id", flat=True))


class FormResponseSerializer(serializers.ModelSerializer):
    form_title = serializers.CharField(source="form_schema.title", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,  # Make user field optional
        default=serializers.CurrentUserDefault(),
    )
    total_score = serializers.FloatField(read_only=True)

    class Meta:
        model = FormResponse
        fields = [
            "id",
            "form_schema",
            "form_title",
            "user",
            "username",
            "response_data",
            "user_journey",
            "flow_step",
            "created_at",
            "updated_at",
            "is_complete",
            "total_score",
        ]
        read_only_fields = ["created_at", "updated_at", "total_score"]

    def validate(self, data):
        """Validate form response against the schema and apply Django validations"""
        form_schema = data.get("form_schema")
        response_data = data.get("response_data")

        if not form_schema or not response_data:
            return data

        try:
            # Use our custom validator that combines JSON Schema and Django validations
            FormValidator.validate_form_data(response_data, form_schema.schema)
            return data
        except JsonSchemaValidationError as e:
            raise serializers.ValidationError(
                f"JSON Schema validation failed: {e.message}"
            ) from e
        except DjangoValidationError as e:
            # Handle Django validation errors and convert to DRF format
            if hasattr(e, "error_dict"):
                # If it's a dictionary of errors
                raise serializers.ValidationError(e.error_dict) from e
            # If it's a list of errors or a single error
            raise serializers.ValidationError(
                e.messages if hasattr(e, "messages") else list(e)
            ) from e

    def create(self, validated_data):
        # Calculate score before saving
        form_schema = validated_data.get("form_schema")
        response_data = validated_data.get("response_data")

        # Create the response object first
        response = super().create(validated_data)

        # Calculate and save the score
        if form_schema and response_data:
            try:
                score = FormScoreCalculator.calculate_score(
                    response_data, form_schema.schema
                )
                response.total_score = score
                response.save(update_fields=["total_score"])
            except Exception as e:
                # Just log error and continue - don't fail the response creation
                print(f"Error calculating score: {e}")

        return response

    def update(self, instance, validated_data):
        # Update the response first
        response = super().update(instance, validated_data)

        # Calculate and update the score if response_data was changed
        if "response_data" in validated_data:
            form_schema = response.form_schema
            response_data = response.response_data

            try:
                score = FormScoreCalculator.calculate_score(
                    response_data, form_schema.schema
                )
                response.total_score = score
                response.save(update_fields=["total_score"])
            except Exception as e:
                # Just log error and continue - don't fail the update
                print(f"Error calculating score: {e}")

        return response


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id"]
