from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import (
    DBFields,
    FlowStep,
    FormFlow,
    FormResponse,
    FormSchema,
    UserJourney,
    WhiteLabel,
)
from .serializers import (
    FlowStepSerializer,
    FormFlowSerializer,
    FormResponseSerializer,
    FormSchemaSerializer,
    UserJourneySerializer,
    WhiteLabelSerializer,
)


class WhiteLabelViewSet(viewsets.ModelViewSet):
    """API endpoint for white labels"""

    queryset = WhiteLabel.objects.filter(is_active=True)
    serializer_class = WhiteLabelSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "created_at"]


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def db_fields_list(request):
    """API endpoint to list all available database field types"""
    fields = [
        {
            "value": field[0],
            "label": field[1],
        }
        for field in DBFields.choices
    ]
    return Response(fields)


class FormSchemaViewSet(viewsets.ModelViewSet):
    """API endpoint for form schemas"""

    queryset = FormSchema.objects.filter(is_active=True)
    serializer_class = FormSchemaSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"])
    def by_white_label(self, request):
        """Get forms filtered by white label"""
        white_label_id = request.query_params.get("white_label_id")
        if not white_label_id:
            return Response(
                {"error": "white_label_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        forms = self.get_queryset().filter(white_label_id=white_label_id)
        serializer = self.get_serializer(forms, many=True)
        return Response(serializer.data)


class FormFlowViewSet(viewsets.ModelViewSet):
    """API endpoint for form flows"""

    queryset = FormFlow.objects.filter(is_active=True)
    serializer_class = FormFlowSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "journey_type"]
    ordering_fields = ["name", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"])
    def by_journey_type(self, request):
        """Get flows filtered by journey type"""
        journey_type = request.query_params.get("journey_type")
        if not journey_type:
            return Response(
                {"error": "journey_type parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        flows = self.get_queryset().filter(journey_type=journey_type)
        serializer = self.get_serializer(flows, many=True)
        return Response(serializer.data)


class FlowStepViewSet(viewsets.ModelViewSet):
    """API endpoint for flow steps"""

    queryset = FlowStep.objects.all()
    serializer_class = FlowStepSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = FlowStep.objects.all()
        flow_id = self.request.query_params.get("flow_id")
        if flow_id:
            queryset = queryset.filter(flow_id=flow_id)
        return queryset


class UserJourneyViewSet(viewsets.ModelViewSet):
    """API endpoint for user journeys"""

    serializer_class = UserJourneySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Admin users can see all journeys, regular users only see their own
        if self.request.user.is_staff:
            queryset = UserJourney.objects.all()
        else:
            queryset = UserJourney.objects.filter(user=self.request.user)

        # Filter by journey type if provided
        journey_type = self.request.query_params.get("journey_type")
        if journey_type:
            queryset = queryset.filter(journey_type=journey_type)

        # Filter upgrade journeys if requested
        is_upgrade = self.request.query_params.get("is_upgrade")
        if is_upgrade is not None:
            is_upgrade = is_upgrade.lower() == "true"
            queryset = queryset.filter(is_upgrade_journey=is_upgrade)

        return queryset

    def perform_create(self, serializer):
        """
        Assign the current user to the journey if not specified and user is not admin
        """
        if not self.request.user.is_staff and not serializer.validated_data.get("user"):
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=["get"])
    def active_journey(self, request):
        """Get the user's active journey of a specific type"""
        journey_type = request.query_params.get("journey_type")
        if not journey_type:
            return Response(
                {"error": "journey_type parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            journey = UserJourney.objects.get(
                user=request.user, journey_type=journey_type, is_complete=False
            )
            serializer = self.get_serializer(journey)
            return Response(serializer.data)
        except UserJourney.DoesNotExist:
            return Response(
                {"message": f"No active {journey_type} journey found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def upgrade_path(self, request):
        """Get the complete upgrade journey path for a user"""
        user_id = request.query_params.get("user_id", request.user.id)

        # Find all journeys that are part of an upgrade process for this user
        upgrade_journeys = UserJourney.objects.filter(
            user_id=user_id, is_upgrade_journey=True
        )

        # Also find journeys that have next steps (part of upgrade path)
        with_next_journeys = UserJourney.objects.filter(
            user_id=user_id, next_journey__isnull=False
        )

        # Combine the results
        all_journeys = upgrade_journeys | with_next_journeys

        serializer = self.get_serializer(all_journeys, many=True)
        return Response(serializer.data)


class FormResponseViewSet(viewsets.ModelViewSet):
    """API endpoint for form responses"""

    serializer_class = FormResponseSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Admin users can see all responses, regular users only see their own
        if self.request.user.is_staff:
            queryset = FormResponse.objects.all()
        else:
            queryset = FormResponse.objects.filter(user=self.request.user)

        # Filter by form schema if provided
        form_schema_id = self.request.query_params.get("form_schema_id")
        if form_schema_id:
            queryset = queryset.filter(form_schema_id=form_schema_id)

        # Filter by user journey if provided
        journey_id = self.request.query_params.get("journey_id")
        if journey_id:
            queryset = queryset.filter(user_journey_id=journey_id)

        return queryset

    def perform_create(self, serializer):
        """
        Assign the current user to the form response if not specified and user is not
        admin
        """
        if not self.request.user.is_staff and not serializer.validated_data.get("user"):
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=["get"])
    def get_user_response(self, request):
        """Get a user's response to a specific form if it exists"""
        form_id = request.query_params.get("form_id")
        if not form_id:
            return Response(
                {"error": "form_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        form_schema = get_object_or_404(FormSchema, pk=form_id, is_active=True)

        # Check if the user has already filled this form
        try:
            response = FormResponse.objects.get(
                form_schema=form_schema, user=request.user
            )
            serializer = self.get_serializer(response)
            return Response(serializer.data)
        except FormResponse.DoesNotExist:
            # Return just the form schema if no response exists
            form_serializer = FormSchemaSerializer(form_schema)
            return Response({"form_schema": form_serializer.data, "response": None})

    @action(detail=False, methods=["get"])
    def journey_responses(self, request):
        """Get all responses for a user journey"""
        journey_id = request.query_params.get("journey_id")
        if not journey_id:
            return Response(
                {"error": "journey_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the user has access to this journey
        journey = get_object_or_404(UserJourney, pk=journey_id)
        if not request.user.is_staff and journey.user != request.user:
            return Response(
                {"error": "You don't have permission to view this journey's responses"},
                status=status.HTTP_403_FORBIDDEN,
            )

        responses = FormResponse.objects.filter(user_journey_id=journey_id)
        serializer = self.get_serializer(responses, many=True)
        return Response(serializer.data)
        # Verify the user has access to this journey
        journey = get_object_or_404(UserJourney, pk=journey_id)
        if not request.user.is_staff and journey.user != request.user:
            return Response(
                {"error": "You don't have permission to view this journey's responses"},
                status=status.HTTP_403_FORBIDDEN,
            )

        responses = FormResponse.objects.filter(user_journey_id=journey_id)
        serializer = self.get_serializer(responses, many=True)
        return Response(serializer.data)
