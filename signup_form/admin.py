from django.contrib import admin

from .models import (
    FlowStep,
    FormFlow,
    FormResponse,
    FormSchema,
    UserJourney,
    WhiteLabel,
)


@admin.register(WhiteLabel)
class WhiteLabelAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(FormSchema)
class FormSchemaAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "white_label",
        "has_ui_schema",
        "created_by",
        "created_at",
        "is_active",
    )
    list_filter = ("is_active", "white_label", "created_at")
    search_fields = ("title", "description")
    date_hierarchy = "created_at"

    def has_ui_schema(self, obj):
        return bool(obj.ui_schema)

    has_ui_schema.boolean = True
    has_ui_schema.short_description = "UI Schema"


@admin.register(FormFlow)
class FormFlowAdmin(admin.ModelAdmin):
    list_display = ("name", "white_label", "journey_type", "created_by", "is_active")
    list_filter = ("is_active", "white_label", "journey_type")
    search_fields = ("name", "description")


@admin.register(FlowStep)
class FlowStepAdmin(admin.ModelAdmin):
    list_display = ("flow", "form_schema", "step_number", "is_required")
    list_filter = ("flow", "is_required")
    search_fields = ("flow__name", "form_schema__title")


@admin.register(UserJourney)
class UserJourneyAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "flow",
        "journey_type",
        "current_step",
        "is_complete",
        "started_at",
    )
    list_filter = ("is_complete", "journey_type", "started_at")
    search_fields = ("user__username", "user__email", "flow__name")
    date_hierarchy = "started_at"


@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):
    list_display = ("form_schema", "user", "user_journey", "created_at", "is_complete")
    list_filter = ("is_complete", "created_at")
    search_fields = ("user__username", "form_schema__title")
    date_hierarchy = "created_at"
