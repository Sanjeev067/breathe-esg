from django.db import models
from django.core.exceptions import ValidationError
from .utils import normalize_emission


# 1. Company (Multi-tenancy)
class Company(models.Model):
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100)

    class Meta:
        app_label = 'emissions'

    def __str__(self):
        return self.name


# 2. Data Source
class DataSource(models.Model):
    SOURCE_CHOICES = [
        ("SAP", "SAP"),
        ("UTILITY", "Utility"),
        ("TRAVEL", "Travel"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="data_sources"
    )

    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'emissions'

    def __str__(self):
        return f"{self.company.name} - {self.source_type}"


# 3. Emission Record
class EmissionRecord(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("FLAGGED", "Flagged"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    SCOPE_CHOICES = [
        ("SCOPE1", "Scope 1"),
        ("SCOPE2", "Scope 2"),
        ("SCOPE3", "Scope 3"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="records"
    )

    source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="records"
    )

    category = models.CharField(max_length=100)

    raw_value = models.FloatField()
    raw_unit = models.CharField(max_length=50)

    normalized_value = models.FloatField(null=True, blank=True)
    normalized_unit = models.CharField(max_length=50, default="kg CO2e")

    record_date = models.DateField()

    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    is_locked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'emissions'

    def __str__(self):
        return f"{self.category} - {self.raw_value}"

    def clean(self):
        super().clean()
        # Enforce that company matches data source company
        if self.source and self.source.company != self.company:
            raise ValidationError("The record's company must match the data source's company.")
        
        # Enforce raw_value must be positive
        if self.raw_value is not None and self.raw_value < 0:
            raise ValidationError("Raw value must be non-negative.")

    def save(self, *args, **kwargs):
        # Trigger validation
        self.clean()

        is_new = self.pk is None
        old_raw_value = None
        status_changed = None
        locked_changed = None

        if not is_new:
            original = EmissionRecord.objects.get(pk=self.pk)
            # Enforce lock check
            if original.is_locked:
                raise ValidationError("This record is locked and cannot be modified.")
            
            old_raw_value = original.raw_value
            if original.status != self.status:
                status_changed = self.status
            if original.is_locked != self.is_locked and self.is_locked:
                locked_changed = True

        # Perform dynamic normalization
        self.normalized_value, self.normalized_unit = normalize_emission(
            self.scope, self.raw_value, self.raw_unit
        )

        # ESG Protocol: If status is set to APPROVED, automatically lock the record
        if self.status == "APPROVED" and not self.is_locked:
            self.is_locked = True
            locked_changed = True

        # Save to database
        super().save(*args, **kwargs)

        # Create audit logs
        if is_new:
            AuditLog.objects.create(
                record=self,
                action="CREATED",
                new_value=self.raw_value
            )
        else:
            # Log value update
            if old_raw_value != self.raw_value:
                AuditLog.objects.create(
                    record=self,
                    action="UPDATED",
                    old_value=old_raw_value,
                    new_value=self.raw_value
                )
            # Log status change
            if status_changed:
                action_map = {
                    "APPROVED": "APPROVED",
                    "REJECTED": "REJECTED"
                }
                action = action_map.get(status_changed)
                if action:
                    AuditLog.objects.create(
                        record=self,
                        action=action,
                        old_value=old_raw_value,
                        new_value=self.raw_value
                    )
            # Log lock change
            if locked_changed:
                AuditLog.objects.create(
                    record=self,
                    action="LOCKED",
                    old_value=old_raw_value,
                    new_value=self.raw_value
                )

    def delete(self, *args, **kwargs):
        # Enforce lock check on deletion
        if self.is_locked:
            raise ValidationError("This record is locked and cannot be deleted.")
        super().delete(*args, **kwargs)


# 4. Audit Log
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("CREATED", "Created"),
        ("UPDATED", "Updated"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("LOCKED", "Locked"),
    ]

    record = models.ForeignKey(
        EmissionRecord,
        on_delete=models.CASCADE,
        related_name="audit_logs"
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )

    old_value = models.FloatField(
        null=True,
        blank=True
    )

    new_value = models.FloatField(
        null=True,
        blank=True
    )

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        app_label = 'emissions'

    def __str__(self):
        return f"{self.record.id} - {self.action}"