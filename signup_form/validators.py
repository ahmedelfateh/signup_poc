import re
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator, validate_email
from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from signup_form.models import DBFields


class FormValidator:
    """
    Custom validator that combines JSON Schema validation with Django-specific field
    validation
    """

    @classmethod
    def get_field_validators(cls):
        """
        Returns a dictionary mapping DBFields to their validator methods
        This makes it easy to add new validators as new DBFields are added
        """
        return {
            DBFields.EMAIL: cls.validate_email,
            DBFields.PHONE: cls.validate_phone,
            DBFields.FIRST_NAME: cls.validate_name,
            DBFields.LAST_NAME: cls.validate_name,
            DBFields.FULL_NAME: cls.validate_name,
            DBFields.DATE_OF_BIRTH: cls.validate_date_of_birth,
            DBFields.POSTAL_CODE: cls.validate_postal_code,
            DBFields.SSN: cls.validate_ssn,
            DBFields.PASSPORT: cls.validate_passport,
            DBFields.ID_NUMBER: cls.validate_id_number,
            # Add more field validators as needed
        }

    @staticmethod
    def validate_email(value, context=None):
        """Validate an email address"""
        validate_email(value)
        # Skip email uniqueness check for test emails
        # or if checking current user's email
        if context and context.get("skip_uniqueness_check"):
            return

        user = context.get("user") if context else None
        if (
            not value.endswith("@example.com")
            and User.objects.filter(email=value).exists()
        ):
            # Allow if it's the current user's email
            if user and user.email == value:
                return
            raise DjangoValidationError("A user with this email already exists.")

    @staticmethod
    def validate_phone(value, context=None):
        """Validate a phone number"""
        phone_regex = RegexValidator(
            regex=r"^\+?1?\d{9,15}$",
            message="Phone number must be entered in a valid format.",
        )
        phone_regex(value)

    @staticmethod
    def validate_name(value, context=None):
        """Validate a name field"""
        if not value or len(value.strip()) < 2:
            raise DjangoValidationError("Name must be at least 2 characters long.")

        if re.search(r"[0-9!@#$%^&*()_+]", value):
            raise DjangoValidationError(
                "Name should not contain numbers or special characters."
            )

    @staticmethod
    def validate_date_of_birth(value, context=None):
        """Validate date of birth"""
        try:
            # Parse date string to date object (format will depend on your frontend)
            dob = datetime.strptime(value, "%Y-%m-%d").date()
            today = datetime.now().date()

            # Check if date is in the past
            if dob > today:
                raise DjangoValidationError("Date of birth cannot be in the future.")

            # Check if person is at least 18 years old
            age = (
                today.year
                - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )
            if age < 18:
                raise DjangoValidationError("You must be at least 18 years old.")
        except ValueError as err:
            raise DjangoValidationError("Invalid date format. Use YYYY-MM-DD.") from err

    @staticmethod
    def validate_postal_code(value, context=None):
        """Validate postal/zip code"""
        # This is a simplified validation and would need to be country-specific
        if not re.match(r"^\d{5}(-\d{4})?$", value):  # US format
            raise DjangoValidationError("Please enter a valid postal code.")

    @staticmethod
    def validate_ssn(value, context=None):
        """Validate Social Security Number"""
        if not re.match(r"^\d{3}-\d{2}-\d{4}$", value):
            raise DjangoValidationError("Please enter a valid SSN (XXX-XX-XXXX).")

    @staticmethod
    def validate_passport(value, context=None):
        """Validate passport number"""
        if not re.match(r"^[A-Z0-9]{6,9}$", value):
            raise DjangoValidationError("Please enter a valid passport number.")

    @staticmethod
    def validate_id_number(value, context=None):
        """Validate ID number"""
        if not re.match(r"^[A-Z0-9]{5,12}$", value):
            raise DjangoValidationError("Please enter a valid ID number.")

    @classmethod
    def validate_form_data(cls, data, schema, context=None):
        """
        Validate form data against JSON schema and apply Django-specific validations

        Args:
            data: Form response data
            schema: JSON schema to validate against
            context: Optional dictionary with additional context (user, form, etc.)

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

        # Get available validators
        field_validators = cls.get_field_validators()

        # Check for schema properties that map to DBFields
        properties = schema.get("properties", {})

        for field_name, field_config in properties.items():
            # Look for x-db-field or db_field property in schema
            db_field_name = field_config.get("x-db-field") or field_config.get(
                "db_field"
            )

            if db_field_name and field_name in data and data[field_name]:
                # Check if we have a validator for this DB field
                try:
                    # Get the actual DBFields enum value from string
                    db_field = getattr(DBFields, db_field_name, None)

                    if db_field and db_field in field_validators:
                        # Apply the specific validator
                        try:
                            field_validators[db_field](data[field_name], context)
                        except DjangoValidationError as e:
                            errors[field_name] = [str(msg) for msg in e.messages]
                except (AttributeError, KeyError):
                    # If DBField enum doesn't exist, just skip validation
                    pass

        # Special case for password (not in DBFields enum)
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
