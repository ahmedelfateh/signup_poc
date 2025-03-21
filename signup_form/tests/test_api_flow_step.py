import pytest
from django.urls import reverse
from rest_framework import status

from signup_form.models import FlowStep


@pytest.mark.django_db
class TestFlowStepAPI:
    """Test cases for the FlowStep API endpoints"""

    def test_list_flow_steps(self, authenticated_client, flow_steps):
        """Test retrieving a list of flow steps"""
        url = reverse("flowstep-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 2  # At least the two steps we created

    def test_retrieve_flow_step(self, authenticated_client, flow_steps):
        """Test retrieving a single flow step"""
        step = flow_steps[0]
        url = reverse("flowstep-detail", kwargs={"pk": step.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["flow"] == step.flow.id
        assert response.data["form_schema"] == step.form_schema.id
        assert response.data["step_number"] == step.step_number
        assert response.data["is_required"] == step.is_required

    def test_create_flow_step(self, admin_client, form_flow, additional_form_schema):
        """Test creating a new flow step"""
        url = reverse("flowstep-list")
        data = {
            "flow": form_flow.id,
            "form_schema": additional_form_schema.id,
            "step_number": 3,  # A new step number that doesn't exist yet
            "is_required": True,
        }

        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["flow"] == data["flow"]
        assert response.data["form_schema"] == data["form_schema"]
        assert response.data["step_number"] == data["step_number"]
        assert FlowStep.objects.filter(flow=form_flow.id, step_number=3).exists()

    def test_update_flow_step(self, admin_client, flow_steps):
        """Test updating an existing flow step"""
        step = flow_steps[0]
        url = reverse("flowstep-detail", kwargs={"pk": step.id})
        data = {
            "flow": step.flow.id,
            "form_schema": step.form_schema.id,
            "step_number": step.step_number,
            "is_required": False,  # Changed from True to False
        }

        response = admin_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert not response.data["is_required"]

        # Refresh from database
        step.refresh_from_db()
        assert not step.is_required

    def test_filter_by_flow(self, authenticated_client, flow_steps, form_flow):
        """Test filtering flow steps by flow ID"""
        url = reverse("flowstep-list")
        response = authenticated_client.get(url, {"flow_id": form_flow.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 2
        assert all(step["flow"] == form_flow.id for step in response.data["results"])
