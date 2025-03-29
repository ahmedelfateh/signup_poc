from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class WhiteLabel(models.Model):
    """Model to represent white labels/tenants using the system"""

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "White Labels"
        ordering = ["name"]


class UserJourneyType(models.TextChoices):
    """Enum to define different user journey types"""

    LEAD = "LEAD", _("Lead")
    DEMO_USER = "DEMO_USER", _("Demo User")
    LIVE_USER = "LIVE_USER", _("Live User")


class DBFields(models.TextChoices):
    """Enum to define common database fields used in forms
    and have a custom validator in the FormValidator class
    and got saved to a real DB model fields not only the FormResponse model
    """

    FIRST_NAME = "FIRST_NAME", _("First Name")
    LAST_NAME = "LAST_NAME", _("Last Name")
    FULL_NAME = "FULL_NAME", _("Full Name")
    EMAIL = "EMAIL", _("Email Address")
    PHONE = "PHONE", _("Phone Number")
    ADDRESS = "ADDRESS", _("Street Address")
    CITY = "CITY", _("City")
    STATE = "STATE", _("State/Province")
    POSTAL_CODE = "POSTAL_CODE", _("Postal/Zip Code")
    COUNTRY = "COUNTRY", _("Country")
    NATIONALITY = "NATIONALITY", _("Nationality")
    DATE_OF_BIRTH = "DATE_OF_BIRTH", _("Date of Birth")
    GENDER = "GENDER", _("Gender")
    OCCUPATION = "OCCUPATION", _("Occupation")
    COMPANY = "COMPANY", _("Company Name")
    WEBSITE = "WEBSITE", _("Website")
    TAX_ID = "TAX_ID", _("Tax ID")
    SSN = "SSN", _("Social Security Number")
    PASSPORT = "PASSPORT", _("Passport Number")
    ID_NUMBER = "ID_NUMBER", _("ID Number")
    MARITAL_STATUS = "MARITAL_STATUS", _("Marital Status")
    EDUCATION = "EDUCATION", _("Education Level")
    INCOME = "INCOME", _("Income Level")


class FormFlow(models.Model):
    """Model to manage sequences of forms"""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    white_label = models.ForeignKey(
        WhiteLabel, on_delete=models.CASCADE, related_name="form_flows"
    )
    journey_type = models.CharField(
        max_length=50, choices=UserJourneyType.choices, default=UserJourneyType.LEAD
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_flows"
    )

    def __str__(self):
        return f"{self.name} - {self.white_label.name} ({self.journey_type})"

    class Meta:
        ordering = ["name"]


class FormSchema(models.Model):
    """Model to store JSON schema definitions for dynamic forms"""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    schema = models.JSONField()
    ui_schema = models.JSONField(
        null=True,
        blank=True,
        help_text=_("Optional UI schema for customizing form rendering and behavior"),
    )
    white_label = models.ForeignKey(
        WhiteLabel, on_delete=models.CASCADE, related_name="form_schemas", null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_forms"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-created_at"]


class FlowStep(models.Model):
    """Model to connect forms to flows and establish step order"""

    flow = models.ForeignKey(FormFlow, on_delete=models.CASCADE, related_name="steps")
    form_schema = models.ForeignKey(
        FormSchema, on_delete=models.CASCADE, related_name="flow_steps"
    )
    step_number = models.PositiveIntegerField()
    is_required = models.BooleanField(default=True)

    class Meta:
        unique_together = ("flow", "step_number")
        ordering = ["flow", "step_number"]

    def __str__(self):
        return f"Step {self.step_number} of {self.flow.name}"


class UserJourney(models.Model):
    """Model to track a user's progress through a specific journey"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="journeys")
    flow = models.ForeignKey(
        FormFlow, on_delete=models.CASCADE, related_name="user_journeys"
    )
    journey_type = models.CharField(
        max_length=50, choices=UserJourneyType.choices, default=UserJourneyType.LEAD
    )
    previous_journey = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_journey",
        help_text="Previous journey in an upgrade flow",
    )
    is_upgrade_journey = models.BooleanField(
        default=False,
        help_text="Indicates if this journey is part of an upgrade process (DEMO→LIVE)",
    )
    current_step = models.ForeignKey(
        FlowStep, on_delete=models.SET_NULL, null=True, related_name="current_users"
    )
    is_complete = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "flow", "journey_type")
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user.username}'s {self.journey_type} journey - {self.flow.name}"

    @property
    def is_in_upgrade_process(self):
        """Returns True if this journey is either part of an upgrade process
        (either the DEMO or LIVE portion)"""
        return self.is_upgrade_journey or self.next_journey.exists()


class FormResponse(models.Model):
    """Model to store user responses to dynamic forms"""

    form_schema = models.ForeignKey(
        FormSchema, on_delete=models.CASCADE, related_name="responses"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="form_responses"
    )
    response_data = models.JSONField()
    user_journey = models.ForeignKey(
        UserJourney, on_delete=models.CASCADE, related_name="form_responses", null=True
    )
    flow_step = models.ForeignKey(
        FlowStep, on_delete=models.SET_NULL, null=True, related_name="responses"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_complete = models.BooleanField(default=False)
    total_score = models.FloatField(
        default=0.0, help_text="Total calculated score for this form response"
    )

    class Meta:
        unique_together = ("flow_step", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}'s response to {self.form_schema.title}"
