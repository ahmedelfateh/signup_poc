from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FlowStepViewSet,
    FormFlowViewSet,
    FormResponseViewSet,
    FormSchemaViewSet,
    UserJourneyViewSet,
    WhiteLabelViewSet,
    db_fields_list,
)

router = DefaultRouter()
router.register(r"white-labels", WhiteLabelViewSet)
router.register(r"schemas", FormSchemaViewSet)
router.register(r"flows", FormFlowViewSet)
router.register(r"steps", FlowStepViewSet)
router.register(r"journeys", UserJourneyViewSet, basename="user-journey")
router.register(r"responses", FormResponseViewSet, basename="form-response")

urlpatterns = [
    path("", include(router.urls)),
    path("db-fields/", db_fields_list, name="db-fields-list"),
]
