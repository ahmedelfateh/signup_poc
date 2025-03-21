import pytest
from django.urls import reverse
from rest_framework import status

from signup_form.models import WhiteLabel


@pytest.mark.django_db
class TestWhiteLabelAPI:
    """Test cases for the WhiteLabel API endpoints"""

    def test_list_white_labels(self, authenticated_client, white_label):
        """Test retrieving a list of white labels"""
        url = reverse("whitelabel-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == white_label.name
        assert response.data["results"][0]["slug"] == white_label.slug

    def test_retrieve_white_label(self, authenticated_client, white_label):
        """Test retrieving a single white label"""
        url = reverse("whitelabel-detail", kwargs={"pk": white_label.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == white_label.name
        assert response.data["slug"] == white_label.slug
        assert response.data["is_active"] == True  # noqa

    def test_create_white_label(self, admin_client):
        """Test creating a new white label"""
        url = reverse("whitelabel-list")
        data = {
            "name": "New Test White Label",
            "slug": "new-test-white-label",
            "is_active": True,
        }

        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == data["name"]
        assert response.data["slug"] == data["slug"]
        assert WhiteLabel.objects.filter(slug="new-test-white-label").exists()

    def test_update_white_label(self, admin_client, white_label):
        """Test updating an existing white label"""
        url = reverse("whitelabel-detail", kwargs={"pk": white_label.id})
        data = {
            "name": "Updated White Label Name",
            "slug": white_label.slug,
            "is_active": white_label.is_active,
        }

        response = admin_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated White Label Name"

        # Refresh from database
        white_label.refresh_from_db()
        assert white_label.name == "Updated White Label Name"

    def test_partial_update_white_label(self, admin_client, white_label):
        """Test partially updating a white label"""
        url = reverse("whitelabel-detail", kwargs={"pk": white_label.id})
        data = {"name": "Partially Updated White Label"}

        response = admin_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Partially Updated White Label"
        assert response.data["slug"] == white_label.slug  # Unchanged

        # Refresh from database
        white_label.refresh_from_db()
        assert white_label.name == "Partially Updated White Label"
