from rest_framework import serializers
from .models import Company, DataSource, EmissionRecord, AuditLog


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = "__all__"


class EmissionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionRecord
        fields = "__all__"
        read_only_fields = ("normalized_value", "normalized_unit", "is_locked", "created_at")

    def validate(self, attrs):
        # Retrieve current instances or input attributes
        company = attrs.get('company', getattr(self.instance, 'company', None))
        source = attrs.get('source', getattr(self.instance, 'source', None))
        raw_value = attrs.get('raw_value', getattr(self.instance, 'raw_value', None))

        # 1. Enforce lock check on update
        if self.instance and self.instance.is_locked:
            raise serializers.ValidationError({"non_field_errors": "This record is locked and cannot be modified."})

        # 2. Enforce company matches source company
        if source and company and source.company != company:
            raise serializers.ValidationError({"source": "The record's company must match the data source's company."})

        # 3. Enforce non-negative raw_value
        if raw_value is not None and raw_value < 0:
            raise serializers.ValidationError({"raw_value": "Raw value must be non-negative."})

        return attrs


class AuditLogSerializer(serializers.ModelSerializer):
    # Include record details in the serialized audit log representation
    class Meta:
        model = AuditLog
        fields = "__all__"