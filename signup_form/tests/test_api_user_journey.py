import pytest
from django.urls import reverse
from rest_framework import status

from signup_form.models import UserJourney


@pytest.mark.django_db
class TestUserJourneyAPI:
    """Test cases for the UserJourney API endpoints"""

    def test_list_user_journeys(self, authenticated_client, user_journey):
        """Test retrieving a list of user journeys"""
        url = reverse("user-journey-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1
        assert any(
            journey["id"] == user_journey.id for journey in response.data["results"]
        )

    def test_retrieve_user_journey(self, authenticated_client, user_journey):
        """Test retrieving a single user journey"""
        url = reverse("user-journey-detail", kwargs={"pk": user_journey.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"] == user_journey.user.id
        assert response.data["flow"] == user_journey.flow.id
        assert response.data["journey_type"] == user_journey.journey_type
        assert response.data["current_step"] == user_journey.current_step.id

    def test_create_user_journey(
        self, authenticated_client, regular_user, form_flow, flow_steps
    ):
        """Test creating a new user journey"""
        # First, delete any existing journey for this user/flow to avoid conflicts
        UserJourney.objects.filter(user=regular_user, flow=form_flow).delete()

        url = reverse("user-journey-list")
        data = {
            "flow": form_flow.id,
            "journey_type": "DEMO_USER",
            "current_step": flow_steps[0].id,
            "is_complete": False,
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"] == regular_user.id
        assert response.data["flow"] == form_flow.id
        assert response.data["journey_type"] == "DEMO_USER"
        assert UserJourney.objects.filter(
            user=regular_user, flow=form_flow, journey_type="DEMO_USER"
        ).exists()

    def test_update_user_journey(self, authenticated_client, user_journey, flow_steps):
        """Test updating an existing user journey"""
        url = reverse("user-journey-detail", kwargs={"pk": user_journey.id})

        # Progress to next step and mark as complete
        data = {
            "user": user_journey.user.id,
            "flow": user_journey.flow.id,
            "journey_type": user_journey.journey_type,
            "current_step": flow_steps[1].id,  # Move to next step
            "is_complete": True,
        }

        response = authenticated_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["current_step"] == flow_steps[1].id
        assert response.data["is_complete"]

        # Refresh from database
        user_journey.refresh_from_db()
        assert user_journey.current_step.id == flow_steps[1].id
        assert user_journey.is_complete

    def test_get_active_journey(self, authenticated_client, user_journey):
        """Test retrieving the active journey for a user"""
        url = reverse("user-journey-active-journey")
        response = authenticated_client.get(
            url, {"journey_type": user_journey.journey_type}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == user_journey.id
        assert response.data["is_complete"] == False  # noqa

    def test_no_active_journey_found(self, authenticated_client):
        """Test response when no active journey exists for the journey type"""
        url = reverse("user-journey-active-journey")
        response = authenticated_client.get(url, {"journey_type": "UPGRADE"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No active UPGRADE journey found" in response.data["message"]

    def test_admin_can_see_all_journeys(self, admin_client, user_journey):
        """Test that admin users can see journeys from all users"""
        url = reverse("user-journey-list")
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1
        assert any(
            journey["id"] == user_journey.id for journey in response.data["results"]
        )

    def test_mark_journey_complete(self, authenticated_client, user_journey):
        """Test marking a journey as complete"""
        url = reverse("user-journey-detail", kwargs={"pk": user_journey.id})
        data = {
            "user": user_journey.user.id,
            "flow": user_journey.flow.id,
            "journey_type": user_journey.journey_type,
            "current_step": user_journey.current_step.id,
            "is_complete": True,
        }

        response = authenticated_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_complete"] == True  # noqa

        # Refresh from database
        user_journey.refresh_from_db()
        assert user_journey.is_complete == True  # noqa

    def test_create_upgrade_journey(
        self, authenticated_client, regular_user, form_flow, flow_steps
    ):
        """Test creating an upgrade journey"""
        # First, delete any existing journey for this user/flow to avoid conflicts
        UserJourney.objects.filter(user=regular_user, flow=form_flow).delete()

        # Create a DEMO_USER journey first
        demo_journey = UserJourney.objects.create(
            user=regular_user,
            flow=form_flow,
            journey_type="DEMO_USER",
            current_step=flow_steps[0],
            is_complete=True,
        )

        # Now create a LIVE_USER journey as an upgrade
        url = reverse("user-journey-list")
        data = {
            "flow": form_flow.id,
            "journey_type": "LIVE_USER",
            "current_step": flow_steps[0].id,
            "is_complete": False,
            "previous_journey": demo_journey.id,
            "is_upgrade_journey": True,
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"] == regular_user.id
        assert response.data["flow"] == form_flow.id
        assert response.data["journey_type"] == "LIVE_USER"
        assert response.data["previous_journey"] == demo_journey.id
        assert response.data["is_upgrade_journey"] == True  # noqa

    def test_get_upgrade_path(
        self, authenticated_client, regular_user, form_flow, flow_steps
    ):
        """Test retrieving a user's upgrade journey path"""
        # First, delete any existing journeys for this user/flow to avoid conflicts
        UserJourney.objects.filter(user=regular_user, flow=form_flow).delete()

        # Create a DEMO_USER journey
        demo_journey = UserJourney.objects.create(
            user=regular_user,
            flow=form_flow,
            journey_type="DEMO_USER",
            current_step=flow_steps[0],
            is_complete=True,
            is_upgrade_journey=True,
        )

        # Create a LIVE_USER journey linked to the DEMO journey
        live_journey = UserJourney.objects.create(
            user=regular_user,
            flow=form_flow,
            journey_type="LIVE_USER",  # Different journey_type
            current_step=flow_steps[0],
            previous_journey=demo_journey,
            is_upgrade_journey=True,
        )

        url = reverse("user-journey-upgrade-path")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        journey_ids = [journey["id"] for journey in response.data]
        assert demo_journey.id in journey_ids
        assert live_journey.id in journey_ids
