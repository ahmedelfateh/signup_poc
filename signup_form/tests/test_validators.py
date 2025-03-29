from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from signup_form.models import DBFields
from signup_form.validators import FormValidator


class TestFormValidator:
    """Test the FormValidator class methods"""

    @pytest.mark.django_db
    def test_validate_email_valid(self):
        """Test valid email addresses"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.com",
            "user+tag@example.co.uk",
        ]
        for email in valid_emails:
            # Should not raise exceptions
            FormValidator.validate_email(email)

    def test_validate_email_invalid(self):
        """Test invalid email addresses"""
        invalid_emails = [
            "not-an-email",
            "missing@domain",
            "@no-local-part.com",
            "spaces in@email.com",
        ]
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                FormValidator.validate_email(email)

    def test_validate_email_uniqueness(self, db):
        """Test email uniqueness validation"""
        # Create a user with a specific email
        email = "existing@example.org"
        User.objects.create(username="testuser", email=email)

        # Should raise for existing email
        with pytest.raises(ValidationError):
            FormValidator.validate_email(email)

        # Should not raise for example.com emails (test emails)
        FormValidator.validate_email("test@example.com")

        # Should not raise when checking user's own email
        context = {"user": MagicMock(email=email),
                   "skip_uniqueness_check": False}
        FormValidator.validate_email(email, context=context)

        # Should not raise when skip_uniqueness_check is True
        context = {"skip_uniqueness_check": True}
        FormValidator.validate_email(email, context=context)

    def test_validate_phone_valid(self):
        """Test valid phone numbers"""
        valid_phones = [
            "+12345678901",
            "123456789012",
            "+442071234567",
        ]
        for phone in valid_phones:
            # Should not raise exceptions
            FormValidator.validate_phone(phone)

    def test_validate_phone_invalid(self):
        """Test invalid phone numbers"""
        invalid_phones = [
            "123",  # too short
            "abcdefghijk",  # not a number
            "+1234$6789",  # invalid character
        ]
        for phone in invalid_phones:
            with pytest.raises(ValidationError):
                FormValidator.validate_phone(phone)

    def test_validate_name_valid(self):
        """Test valid names"""
        valid_names = [
            "John",
            "Mary Jane",
            "Jean-Claude",
            "O'Connor",
        ]
        for name in valid_names:
            # Should not raise exceptions
            FormValidator.validate_name(name)

    def test_validate_name_invalid(self):
        """Test invalid names"""
        invalid_names = [
            "J",  # too short
            "John123",  # contains numbers
            "Mary$Jane",  # contains special chars
            "",  # empty
        ]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                FormValidator.validate_name(name)

    def test_validate_date_of_birth_valid(self):
        """Test valid dates of birth"""
        # 30 years ago
        valid_date = (datetime.now() - timedelta(days=365*30)
                      ).strftime("%Y-%m-%d")
        # Should not raise exceptions
        FormValidator.validate_date_of_birth(valid_date)

    def test_validate_date_of_birth_invalid(self):
        """Test invalid dates of birth"""
        # Future date
        future_date = (datetime.now() + timedelta(days=10)
                       ).strftime("%Y-%m-%d")
        with pytest.raises(ValidationError) as exc:
            FormValidator.validate_date_of_birth(future_date)
        assert "cannot be in the future" in str(exc.value)

        # Underage - 17 years ago
        underage_date = (datetime.now() - timedelta(days=365*17)
                         ).strftime("%Y-%m-%d")
        with pytest.raises(ValidationError) as exc:
            FormValidator.validate_date_of_birth(underage_date)
        assert "at least 18 years old" in str(exc.value)

        # Invalid format
        with pytest.raises(ValidationError) as exc:
            FormValidator.validate_date_of_birth("2000/01/01")
        assert "Invalid date format" in str(exc.value)

    def test_validate_postal_code_valid(self):
        """Test valid postal codes"""
        valid_codes = [
            "12345",
            "12345-6789"
        ]
        for code in valid_codes:
            # Should not raise exceptions
            FormValidator.validate_postal_code(code)

    def test_validate_postal_code_invalid(self):
        """Test invalid postal codes"""
        invalid_codes = [
            "1234",  # too short
            "123456",  # wrong format
            "12345-67",  # wrong format
            "abcde",  # not numeric
        ]
        for code in invalid_codes:
            with pytest.raises(ValidationError):
                FormValidator.validate_postal_code(code)

    def test_validate_ssn_valid(self):
        """Test valid SSNs"""
        FormValidator.validate_ssn("123-45-6789")

    def test_validate_ssn_invalid(self):
        """Test invalid SSNs"""
        invalid_ssns = [
            "123456789",  # missing hyphens
            "12-34-5678",  # wrong format
            "123-45-67a",  # non-numeric
        ]
        for ssn in invalid_ssns:
            with pytest.raises(ValidationError):
                FormValidator.validate_ssn(ssn)

    def test_validate_passport_valid(self):
        """Test valid passport numbers"""
        valid_passports = [
            "A12345",
            "ABC1234",
            "AB123456"
        ]
        for passport in valid_passports:
            # Should not raise exceptions
            FormValidator.validate_passport(passport)

    def test_validate_passport_invalid(self):
        """Test invalid passport numbers"""
        invalid_passports = [
            "A1234",  # too short
            "ABCDEFGHIJK",  # too long
            "ab12345",  # lowercase not allowed
            "A!12345",  # special chars
        ]
        for passport in invalid_passports:
            with pytest.raises(ValidationError):
                FormValidator.validate_passport(passport)

    def test_validate_id_number_valid(self):
        """Test valid ID numbers"""
        valid_ids = [
            "A1234",
            "AB12345",
            "ABC123456789"
        ]
        for id_num in valid_ids:
            # Should not raise exceptions
            FormValidator.validate_id_number(id_num)

    def test_validate_id_number_invalid(self):
        """Test invalid ID numbers"""
        invalid_ids = [
            "A123",  # too short
            "ABCDEFGHIJKLM",  # too long
            "abc12345",  # lowercase not allowed
            "A!12345",  # special chars
        ]
        for id_num in invalid_ids:
            with pytest.raises(ValidationError):
                FormValidator.validate_id_number(id_num)

    def test_validate_form_data_valid(self):
        """Test form data validation with valid data"""
        # Simple schema for testing
        schema = {
            "type": "object",
            "properties": {
                "email": {"type": "string", "x-db-field": "EMAIL"},
                "first_name": {"type": "string", "x-db-field": "FIRST_NAME"},
                "dob": {"type": "string", "x-db-field": "DATE_OF_BIRTH"},
            },
            "required": ["email", "first_name"]
        }

        # Valid data matching schema
        data = {
            "email": "test@example.com",
            "first_name": "John",
            "dob": (datetime.now() - timedelta(days=365*30)).strftime("%Y-%m-%d")
        }

        # Should not raise exceptions
        result = FormValidator.validate_form_data(data, schema)
        assert result == data

    def test_validate_form_data_invalid_schema(self):
        """Test form data that doesn't match the schema"""
        schema = {
            "type": "object",
            "properties": {
                "email": {"type": "string", "x-db-field": "EMAIL"},
                "age": {"type": "integer", "minimum": 18}
            },
            "required": ["email", "age"]
        }

        # Missing required field
        invalid_data = {
            "email": "test@example.com"
        }

        with pytest.raises(ValidationError) as exc:
            FormValidator.validate_form_data(invalid_data, schema)
        assert "JSON Schema validation failed" in str(exc.value)

    def test_validate_form_data_invalid_fields(self):
        """Test form data with invalid field values"""
        schema = {
            "type": "object",
            "properties": {
                "email": {"type": "string", "x-db-field": "EMAIL"},
                "first_name": {"type": "string", "x-db-field": "FIRST_NAME"}
            }
        }

        # Invalid email
        invalid_data = {
            "email": "not-an-email",
            "first_name": "John"
        }

        with pytest.raises(ValidationError):
            FormValidator.validate_form_data(invalid_data, schema)

        # Invalid name
        invalid_data = {
            "email": "test@example.com",
            "first_name": "J1"  # Contains a number
        }

        with pytest.raises(ValidationError):
            FormValidator.validate_form_data(invalid_data, schema)

    def test_password_validation(self):
        """Test password validation in form data"""
        schema = {
            "type": "object",
            "properties": {
                "password": {"type": "string"}
            }
        }

        # Simple weak password
        data = {
            "password": "123"
        }

        # With mocked validate_password to test the error handling
        with patch('signup_form.validators.validate_password', side_effect=ValidationError('Too weak')):
            with pytest.raises(ValidationError) as exc:
                FormValidator.validate_form_data(data, schema)
            assert 'password' in str(exc.value)
