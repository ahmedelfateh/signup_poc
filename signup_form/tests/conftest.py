import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from signup_form.models import (
    FlowStep,
    FormFlow,
    FormResponse,
    FormSchema,
    UserJourney,
    WhiteLabel,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    user = User.objects.create_user(
        username="admin",
        email="admin@example.com",
        password="adminpassword",
        is_staff=True,
        is_superuser=True,
    )
    return user


@pytest.fixture
def regular_user():
    user = User.objects.create_user(
        username="testuser", email="test@example.com", password="testpassword"
    )
    return user


@pytest.fixture
def authenticated_client(api_client, regular_user):
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def white_label():
    return WhiteLabel.objects.create(
        name="Test White Label", slug="test-white-label", is_active=True
    )


@pytest.fixture
def form_schema(white_label, admin_user):
    return FormSchema.objects.create(
        title="Contact Information",
        description="Basic contact information form",
        white_label=white_label,
        created_by=admin_user,
        schema={
            "type": "object",
            "required": ["firstName", "lastName", "email"],
            "properties": {
                "firstName": {"type": "string", "title": "First Name"},
                "lastName": {"type": "string", "title": "Last Name"},
                "email": {"type": "string", "format": "email", "title": "Email"},
                "phoneNumber": {"type": "string", "title": "Phone Number"},
            },
        },
    )


@pytest.fixture
def additional_form_schema(white_label, admin_user):
    return FormSchema.objects.create(
        title="Address Information",
        description="Address form",
        white_label=white_label,
        created_by=admin_user,
        schema={
            "type": "object",
            "required": ["streetAddress", "city"],
            "properties": {
                "streetAddress": {"type": "string", "title": "Street Address"},
                "city": {"type": "string", "title": "City"},
                "postalCode": {"type": "string", "title": "Postal Code"},
            },
        },
    )


@pytest.fixture
def form_flow(white_label, admin_user):
    return FormFlow.objects.create(
        name="Lead Registration Flow",
        description="Flow for collecting lead information",
        white_label=white_label,
        journey_type="LEAD",
        created_by=admin_user,
    )


@pytest.fixture
def flow_steps(form_flow, form_schema, additional_form_schema):
    step1 = FlowStep.objects.create(
        flow=form_flow, form_schema=form_schema, step_number=1, is_required=True
    )
    step2 = FlowStep.objects.create(
        flow=form_flow,
        form_schema=additional_form_schema,
        step_number=2,
        is_required=True,
    )
    return [step1, step2]


@pytest.fixture
def user_journey(regular_user, form_flow, flow_steps):
    journey = UserJourney.objects.create(
        user=regular_user,
        flow=form_flow,
        journey_type="LEAD",
        current_step=flow_steps[0],
    )
    return journey


@pytest.fixture
def form_response(regular_user, form_schema, user_journey, flow_steps):
    """Create a sample form response for testing"""
    response = FormResponse.objects.create(
        form_schema=form_schema,
        user=regular_user,
        response_data={
            "firstName": "Test",
            "lastName": "User",
            "email": "testuser@example.com",
            "phoneNumber": "555-5555",
        },
        user_journey=user_journey,
        flow_step=flow_steps[0],
        is_complete=True,
    )
    return response


@pytest.fixture
def upgrade_user_journey(regular_user, form_flow, flow_steps):
    """Create a journey for the upgrade path"""
    # First create a demo journey
    demo_journey = UserJourney.objects.create(
        user=regular_user,
        flow=form_flow,
        journey_type="DEMO_USER",
        current_step=flow_steps[0],
        is_complete=True,
        is_upgrade_journey=True,
    )

    # Then create a live journey that references the demo journey
    live_journey = UserJourney.objects.create(
        user=regular_user,
        flow=form_flow,
        journey_type="LIVE_USER",
        current_step=flow_steps[0],
        previous_journey=demo_journey,
        is_upgrade_journey=True,
    )

    return {"demo": demo_journey, "live": live_journey}
