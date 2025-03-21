import pytest
from django.urls import reverse
from rest_framework import status

from signup_form.models import FormSchema


@pytest.mark.django_db
class TestFormSchemaAPI:
    """Test cases for the FormSchema API endpoints"""

    def test_list_form_schemas(self, authenticated_client, form_schema):
        """Test retrieving a list of form schemas"""
        url = reverse("formschema-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1
        assert any(
            schema["title"] == form_schema.title for schema in response.data["results"]
        )

    def test_retrieve_form_schema(self, authenticated_client, form_schema):
        """Test retrieving a single form schema"""
        url = reverse("formschema-detail", kwargs={"pk": form_schema.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == form_schema.title
        assert response.data["description"] == form_schema.description
        assert response.data["schema"] == form_schema.schema
        assert response.data["white_label"] == form_schema.white_label.id

    def test_create_form_schema(self, admin_client, white_label):
        """Test creating a new form schema"""
        url = reverse("formschema-list")
        data = {
            "title": "New Test Form",
            "description": "A test form schema",
            "white_label": white_label.id,
            "schema": {
                "type": "object",
                "properties": {"testField": {"type": "string", "title": "Test Field"}},
            },
            "is_active": True,
        }

        response = admin_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == data["title"]
        assert FormSchema.objects.filter(title="New Test Form").exists()

    def test_create_form_schema_with_ui_schema(self, admin_client, white_label):
        """Test creating a new form schema with UI schema"""
        url = reverse("formschema-list")
        data = {
            "title": "Form With UI Schema",
            "description": "A test form schema with UI configuration",
            "white_label": white_label.id,
            "schema": {
                "type": "object",
                "properties": {"testField": {"type": "string", "title": "Test Field"}},
            },
            "ui_schema": {
                "testField": {
                    "ui:widget": "textarea",
                    "ui:placeholder": "Enter test data here",
                    "ui:autofocus": True,
                }
            },
            "is_active": True,
        }

        response = admin_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == data["title"]
        assert response.data["ui_schema"] == data["ui_schema"]
        assert FormSchema.objects.filter(title="Form With UI Schema").exists()

        # Retrieve the created object and verify UI schema was saved
        form_schema = FormSchema.objects.get(title="Form With UI Schema")
        assert form_schema.ui_schema is not None
        assert "testField" in form_schema.ui_schema

    def test_update_form_schema(self, admin_client, form_schema):
        """Test updating an existing form schema"""
        url = reverse("formschema-detail", kwargs={"pk": form_schema.id})
        data = {
            "title": "Updated Form Schema",
            "description": form_schema.description,
            "white_label": form_schema.white_label.id,
            "schema": form_schema.schema,
            "is_active": form_schema.is_active,
        }

        response = admin_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated Form Schema"

        # Refresh from database
        form_schema.refresh_from_db()
        assert form_schema.title == "Updated Form Schema"

    def test_filter_by_white_label(
        self, authenticated_client, form_schema, white_label
    ):
        """Test filtering form schemas by white label"""
        url = reverse("formschema-by-white-label")
        response = authenticated_client.get(url, {"white_label_id": white_label.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert any(schema["title"] == form_schema.title for schema in response.data)

    def test_missing_white_label_param(self, authenticated_client):
        """Test error response when white_label_id parameter is missing"""
        url = reverse("formschema-by-white-label")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "white_label_id parameter is required" in response.data["error"]

    def test_invalid_schema_validation(self, admin_client, white_label):
        """Test validation of form schema structure"""
        url = reverse("formschema-list")
        data = {
            "title": "Invalid Schema Form",
            "description": "A form with invalid schema",
            "white_label": white_label.id,
            "schema": {
                # Missing required 'type' field
                "properties": {"testField": {"type": "string", "title": "Test Field"}}
            },
            "is_active": True,
        }

        response = admin_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # The error message is nested within the schema field errors
        assert "schema" in response.data
        assert "Invalid schema format" in str(response.data["schema"])

        # Extract the raw error detail string to check the actual message
        error_detail_string = str(response.data["schema"][0])
        assert "Schema must contain 'type' field" in error_detail_string
