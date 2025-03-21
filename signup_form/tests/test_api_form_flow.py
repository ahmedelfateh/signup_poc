import pytest
from django.urls import reverse
from rest_framework import status

from signup_form.models import FormFlow


@pytest.mark.django_db
class TestFormFlowAPI:
    """Test cases for the FormFlow API endpoints"""

    def test_list_form_flows(self, authenticated_client, form_flow):
        """Test retrieving a list of form flows"""
        url = reverse("formflow-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1
        assert any(flow["name"] == form_flow.name for flow in response.data["results"])

    def test_retrieve_form_flow(self, authenticated_client, form_flow):
        """Test retrieving a single form flow"""
        url = reverse("formflow-detail", kwargs={"pk": form_flow.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == form_flow.name
        assert response.data["description"] == form_flow.description
        assert response.data["white_label"] == form_flow.white_label.id
        assert response.data["journey_type"] == form_flow.journey_type

    def test_create_form_flow(self, admin_client, white_label):
        """Test creating a new form flow"""
        url = reverse("formflow-list")
        data = {
            "name": "New Test Flow",
            "description": "A test form flow",
            "white_label": white_label.id,
            "journey_type": "DEMO_USER",
            "is_active": True,
        }

        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == data["name"]
        assert response.data["journey_type"] == data["journey_type"]
        assert FormFlow.objects.filter(name="New Test Flow").exists()

    def test_update_form_flow(self, admin_client, form_flow):
        """Test updating an existing form flow"""
        url = reverse("formflow-detail", kwargs={"pk": form_flow.id})
        data = {
            "name": "Updated Flow Name",
            "description": form_flow.description,
            "white_label": form_flow.white_label.id,
            "journey_type": form_flow.journey_type,
            "is_active": form_flow.is_active,
        }

        response = admin_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Flow Name"

        # Refresh from database
        form_flow.refresh_from_db()
        assert form_flow.name == "Updated Flow Name"

    def test_filter_by_journey_type(self, authenticated_client, form_flow):
        """Test filtering form flows by journey type"""
        url = reverse("formflow-by-journey-type")
        response = authenticated_client.get(
            url, {"journey_type": form_flow.journey_type}
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert any(flow["name"] == form_flow.name for flow in response.data)

    def test_missing_journey_type_param(self, authenticated_client):
        """Test error response when journey_type parameter is missing"""
        url = reverse("formflow-by-journey-type")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "journey_type parameter is required" in response.data["error"]

    def test_deactivate_form_flow(self, admin_client, form_flow):
        """Test deactivating a form flow"""
        url = reverse("formflow-detail", kwargs={"pk": form_flow.id})
        data = {
            "name": form_flow.name,
            "description": form_flow.description,
            "white_label": form_flow.white_label.id,
            "journey_type": form_flow.journey_type,
            "is_active": False,  # Deactivating the flow
        }

        response = admin_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert not response.data["is_active"]

        # Refresh from database
        form_flow.refresh_from_db()
        assert not form_flow.is_active
