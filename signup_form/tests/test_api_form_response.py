import pytest
from django.urls import reverse
from rest_framework import status

from signup_form.models import FormResponse


@pytest.mark.django_db
class TestFormResponseAPI:
    """Test cases for the FormResponse API endpoints"""

    def test_create_form_response(
        self, authenticated_client, regular_user, form_schema, user_journey, flow_steps
    ):
        """Test creating a new form response"""
        url = reverse("form-response-list")
        data = {
            "form_schema": form_schema.id,
            "response_data": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john.doe@example.com",
                "phoneNumber": "555-1234",
            },
            "user_journey": user_journey.id,
            "flow_step": flow_steps[0].id,
            "is_complete": True,
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["form_schema"] == form_schema.id
        assert response.data["response_data"]["firstName"] == "John"
        assert response.data["response_data"]["lastName"] == "Doe"
        assert FormResponse.objects.filter(
            form_schema=form_schema.id, user=regular_user, flow_step=flow_steps[0].id
        ).exists()

    def test_list_form_responses(
        self, authenticated_client, regular_user, form_schema, user_journey, flow_steps
    ):
        """Test retrieving a list of form responses"""
        # First, create a response
        FormResponse.objects.create(
            form_schema=form_schema,
            user=regular_user,
            response_data={
                "firstName": "Jane",
                "lastName": "Smith",
                "email": "jane@example.com",
            },
            user_journey=user_journey,
            flow_step=flow_steps[0],
            is_complete=True,
        )

        url = reverse("form-response-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1
        # Verify we can see our response data
        assert any(
            "Jane" in str(resp["response_data"]) for resp in response.data["results"]
        )

    def test_retrieve_form_response(
        self, authenticated_client, regular_user, form_schema, user_journey, flow_steps
    ):
        """Test retrieving a single form response"""
        # Create a response first
        form_response = FormResponse.objects.create(
            form_schema=form_schema,
            user=regular_user,
            response_data={
                "firstName": "Robert",
                "lastName": "Johnson",
                "email": "robert@example.com",
            },
            user_journey=user_journey,
            flow_step=flow_steps[0],
            is_complete=True,
        )

        url = reverse("form-response-detail", kwargs={"pk": form_response.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["response_data"]["firstName"] == "Robert"
        assert response.data["response_data"]["lastName"] == "Johnson"
        assert response.data["form_schema"] == form_schema.id

    def test_get_user_response(self, authenticated_client, regular_user, form_schema):
        """Test getting a user's response to a specific form"""
        # Create a response first
        FormResponse.objects.create(
            form_schema=form_schema,
            user=regular_user,
            response_data={
                "firstName": "Alice",
                "lastName": "Wonder",
                "email": "alice@example.com",
            },
            is_complete=True,
        )

        url = reverse("form-response-get-user-response")
        response = authenticated_client.get(url, {"form_id": form_schema.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["form_schema"] == form_schema.id
        assert response.data["response_data"]["firstName"] == "Alice"
        assert response.data["response_data"]["lastName"] == "Wonder"

    def test_journey_responses(
        self, authenticated_client, regular_user, form_schema, user_journey, flow_steps
    ):
        """Test getting all responses for a user journey"""
        # Create a response first
        FormResponse.objects.create(
            form_schema=form_schema,
            user=regular_user,
            response_data={
                "firstName": "Michael",
                "lastName": "Brown",
                "email": "michael@example.com",
            },
            user_journey=user_journey,
            flow_step=flow_steps[0],
            is_complete=True,
        )

        url = reverse("form-response-journey-responses")
        response = authenticated_client.get(url, {"journey_id": user_journey.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert any("Michael" in str(resp["response_data"]) for resp in response.data)

    def test_form_response_with_invalid_data(
        self, authenticated_client, regular_user, form_schema, user_journey, flow_steps
    ):
        """Test validation of form response data against schema"""
        url = reverse("form-response-list")
        data = {
            "form_schema": form_schema.id,
            "response_data": {
                # Missing required fields according to the schema in conftest.py
                "email": "not-an-email"  # Invalid email format
            },
            "user_journey": user_journey.id,
            "flow_step": flow_steps[0].id,
            "is_complete": True,
        }

        response = authenticated_client.post(url, data, format="json")

        # Should fail validation
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_sees_all_responses(self, admin_client, form_response):
        """Test that admin users can see form responses from all users"""
        url = reverse("form-response-list")
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_update_form_response(
        self, authenticated_client, regular_user, form_schema, user_journey, flow_steps
    ):
        """Test updating an existing form response"""
        # First create a response
        form_response = FormResponse.objects.create(
            form_schema=form_schema,
            user=regular_user,
            response_data={
                "firstName": "Original",
                "lastName": "Name",
                "email": "original@example.com",
            },
            user_journey=user_journey,
            flow_step=flow_steps[0],
            is_complete=False,
        )

        url = reverse("form-response-detail", kwargs={"pk": form_response.id})
        updated_data = {
            "form_schema": form_schema.id,
            "user": regular_user.id,
            "response_data": {
                "firstName": "Updated",
                "lastName": "Name",
                "email": "updated@example.com",
            },
            "user_journey": user_journey.id,
            "flow_step": flow_steps[0].id,
            "is_complete": True,
        }

        response = authenticated_client.put(url, updated_data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["response_data"]["firstName"] == "Updated"
        assert response.data["response_data"]["email"] == "updated@example.com"
        assert response.data["is_complete"]

        # Refresh from database
        form_response.refresh_from_db()
        assert form_response.response_data["firstName"] == "Updated"
        assert form_response.is_complete

    def test_form_response_with_score_calculation(
        self, authenticated_client, regular_user, admin_client, white_label, flow_steps
    ):
        """Test that form responses correctly calculate and save scores"""
        # First, create a schema with scoring
        schema_data = {
            "title": "Test Form with Scoring",
            "description": "Form with scoring fields",
            "white_label": white_label.id,
            "schema": {
                "type": "object",
                "properties": {
                    "nationality": {
                        "type": "string",
                        "enum": ["DE", "IT", "JP", "US", "RU", "Other"],
                        "score": [
                            {"DE": 1},
                            {"IT": 0},
                            {"JP": 2},
                            {"US": 3},
                            {"RU": 1},
                            {"Other": 0},
                        ],
                        "score_type": "normal",
                    },
                    "experience": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "expert"],
                        "score": [{"beginner": 1}, {"intermediate": 2}, {"expert": 3}],
                    },
                },
            },
            "is_active": True,
        }

        url_schema = reverse("formschema-list")
        schema_response = admin_client.post(url_schema, schema_data, format="json")
        assert schema_response.status_code == status.HTTP_201_CREATED
        form_schema_id = schema_response.data["id"]

        # Create a form response with scorable answers
        url = reverse("form-response-list")
        data = {
            "form_schema": form_schema_id,
            "response_data": {"nationality": "JP", "experience": "expert"},
            "is_complete": True,
            "user": regular_user.id,  # Add the user ID to the request
            "flow_step": flow_steps[0].id,
        }

        response = authenticated_client.post(url, data, format="json")

        # For debugging if it still fails
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response content: {response.content}")

        assert response.status_code == status.HTTP_201_CREATED
        assert "total_score" in response.data
        assert response.data["total_score"] == 5.0  # 2 for JP + 3 for expert

        # Verify the score was saved to database
        form_response = FormResponse.objects.get(id=response.data["id"])
        assert form_response.total_score == 5.0

    def test_form_response_with_weighted_scoring(
        self, authenticated_client, regular_user, admin_client, white_label, flow_steps
    ):
        """Test form responses with weighted scoring calculation"""
        # Create a schema with weighted scoring
        schema_data = {
            "title": "Weighted Scoring Form",
            "description": "Form with weighted scoring fields",
            "white_label": white_label.id,
            "schema": {
                "type": "object",
                "properties": {
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "score": [
                            {"low": 5, "weight": 0.5},
                            {"medium": 10, "weight": 1.0},
                            {"high": 15, "weight": 1.5},
                        ],
                        "score_type": "weighted",
                    },
                    "income": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "score": [{"low": 1}, {"medium": 3}, {"high": 5}],
                        "score_type": "normal",
                    },
                },
            },
            "is_active": True,
        }

        url_schema = reverse("formschema-list")
        schema_response = admin_client.post(url_schema, schema_data, format="json")
        assert schema_response.status_code == status.HTTP_201_CREATED
        form_schema_id = schema_response.data["id"]

        # Create a response with both weighted and normal scored fields
        url = reverse("form-response-list")
        data = {
            "form_schema": form_schema_id,
            "response_data": {"risk_level": "high", "income": "medium"},
            "is_complete": True,
            "user": regular_user.id,
            "flow_step": flow_steps[0].id,
        }

        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        # Check the total score: (15 * 1.5) + 3 = 25.5
        assert "total_score" in response.data
        assert response.data["total_score"] == 25.5

        # Verify score is saved correctly in database
        form_response = FormResponse.objects.get(id=response.data["id"])
        assert form_response.total_score == 25.5

    def test_update_response_recalculates_score(
        self, authenticated_client, regular_user, admin_client, white_label, flow_steps
    ):
        """Test that updating a form response recalculates the score"""
        # Create a schema with scoring
        schema_data = {
            "title": "Update Score Test Form",
            "description": "Testing score recalculation on update",
            "white_label": white_label.id,
            "schema": {
                "type": "object",
                "properties": {
                    "rating": {
                        "type": "string",
                        "enum": ["poor", "fair", "good", "excellent"],
                        "score": [
                            {"poor": 1},
                            {"fair": 2},
                            {"good": 3},
                            {"excellent": 4},
                        ],
                    },
                },
            },
            "is_active": True,
        }

        url_schema = reverse("formschema-list")
        schema_response = admin_client.post(url_schema, schema_data, format="json")
        form_schema_id = schema_response.data["id"]

        # Create initial form response
        url = reverse("form-response-list")
        data = {
            "form_schema": form_schema_id,
            "response_data": {"rating": "fair"},
            "is_complete": True,
            "user": regular_user.id,
            "flow_step": flow_steps[0].id,
        }

        response = authenticated_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["total_score"] == 2.0

        # Now update the response
        update_url = reverse("form-response-detail", kwargs={"pk": response.data["id"]})
        update_data = {
            "form_schema": form_schema_id,
            "response_data": {"rating": "excellent"},
            "is_complete": True,
            "user": regular_user.id,
            "flow_step": flow_steps[0].id,
        }

        update_response = authenticated_client.put(
            update_url, update_data, format="json"
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.data["total_score"] == 4.0

        # Verify the updated score in database
        form_response = FormResponse.objects.get(id=response.data["id"])
        assert form_response.total_score == 4.0
