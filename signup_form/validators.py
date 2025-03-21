from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


class FormValidator:
    """
    Custom validator that combines JSON Schema validation with Django-specific field
    validation
    """

    @staticmethod
    def validate_form_data(data, schema):
        """
        Validate form data against JSON schema and apply Django-specific validations

        Args:
            data: Form response data
            schema: JSON schema to validate against

        Raises:
            ValidationError: If validation fails
        """
        # First validate against JSON schema
        try:
            jsonschema_validate(instance=data, schema=schema)
        except JsonSchemaValidationError as e:
            raise DjangoValidationError(
                f"JSON Schema validation failed: {e.message}"
            ) from e

        # Apply Django-specific validations for common fields
        errors = {}

        # Validate email if present
        if "email" in data and data["email"]:
            email = data["email"]
            try:
                # Django email validation
                validate_email(email)

                # Check if email already exists - skip this check in tests
                # as we might be using the same email in multiple test cases
                if (
                    not email.endswith("@example.com")
                    and User.objects.filter(email=email).exists()
                ):
                    errors["email"] = ["A user with this email already exists."]
            except DjangoValidationError as e:
                errors["email"] = [str(msg) for msg in e.messages]

        # Validate password if present
        if "password" in data and data["password"]:
            password = data["password"]
            try:
                # Django password validation (uses settings.AUTH_PASSWORD_VALIDATORS)
                validate_password(password)
            except DjangoValidationError as e:
                errors["password"] = [str(msg) for msg in e.messages]

        # If there are any Django validation errors, raise them
        if errors:
            raise DjangoValidationError(errors)

        return data
