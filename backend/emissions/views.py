from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Sum
from django.db.models.functions import TruncMonth
import csv, json, io
from django.utils import timezone
from pypdf import PdfReader

from .models import Company, DataSource, EmissionRecord, AuditLog
from .serializers import (
    CompanySerializer,
    DataSourceSerializer,
    EmissionRecordSerializer,
    AuditLogSerializer
)


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Company management.
    Provides standard CRUD operations.
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


class DataSourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DataSource management.
    Provides standard CRUD operations.
    """
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer


class EmissionRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EmissionRecord management.
    Provides CRUD, approval controls, and advanced aggregated analytics.
    """
    queryset = EmissionRecord.objects.all().order_by('-record_date')
    serializer_class = EmissionRecordSerializer

    def get_queryset(self):
        """
        Extends standard queryset with robust URL query parameter filtering.
        Used by list views and aggregated analytics.
        """
        queryset = super().get_queryset()
        company_id = self.request.query_params.get('company')
        scope = self.request.query_params.get('scope')
        status_param = self.request.query_params.get('status')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if company_id:
            queryset = queryset.filter(company_id=company_id)
        if scope:
            queryset = queryset.filter(scope=scope)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if start_date:
            queryset = queryset.filter(record_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(record_date__lte=end_date)
        return queryset

    def perform_destroy(self, instance):
        """
        Catches model-level validation error on deleting locked records.
        """
        try:
            instance.delete()
        except DjangoValidationError as e:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError({"detail": str(e.message if hasattr(e, 'message') else e)})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approves an emission record. This sets the status to APPROVED
        which triggers record-locking automatically.
        """
        record = self.get_object()
        try:
            record.status = "APPROVED"
            record.save()
            serializer = self.get_serializer(record)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response(
                {"detail": str(e.message if hasattr(e, 'message') else e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Rejects an emission record. Sets the status to REJECTED.
        """
        record = self.get_object()
        try:
            record.status = "REJECTED"
            record.save()
            serializer = self.get_serializer(record)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response(
                {"detail": str(e.message if hasattr(e, 'message') else e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """
        Explicitly locks a record to prevent any future tampering.
        """
        record = self.get_object()
        try:
            record.is_locked = True
            record.save()
            serializer = self.get_serializer(record)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response(
                {"detail": str(e.message if hasattr(e, 'message') else e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], url_path='upload/sap')
    def upload_sap(self, request):
        """Accept a CSV file for SAP fuel/procurement data and create records."""
        file = request.FILES.get('file')
        if not file:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            decoded = file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            created = []
            for row in reader:
                # Expected columns: company, source, category, raw_value, raw_unit, record_date, scope
                company = Company.objects.get(name=row['company'])
                source_obj, _ = DataSource.objects.get_or_create(company=company, source_type='SAP')
                record = EmissionRecord.objects.create(
                    company=company,
                    source=source_obj,
                    category=row.get('category', ''),
                    raw_value=float(row.get('raw_value', 0)),
                    raw_unit=row.get('raw_unit', ''),
                    record_date=row.get('record_date'),
                    scope=row.get('scope', 'SCOPE1'),
                    status='PENDING'
                )
                created.append(record.id)
            return Response({"created_ids": created}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='upload/utility')
    def upload_utility(self, request):
        """Accept a PDF utility bill, extract text, and create a record (demo implementation)."""
        file = request.FILES.get('file')
        if not file:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Simple PDF text extraction
            pdf_reader = PdfReader(io.BytesIO(file.read()))
            text = "\n".join(page.extract_text() or '' for page in pdf_reader.pages)
            # Very naive parsing – expect lines like "Company: XYZ; Category: Electricity; Value: 123; Unit: kWh; Date: 2023-01-01; Scope: SCOPE2"
            created = []
            for line in text.split('\n'):
                if not line.strip():
                    continue
                parts = {p.split(':')[0].strip().lower(): p.split(':')[1].strip() for p in line.split(';') if ':' in p}
                company = Company.objects.get(name=parts.get('company'))
                source_obj, _ = DataSource.objects.get_or_create(company=company, source_type='UTILITY')
                record = EmissionRecord.objects.create(
                    company=company,
                    source=source_obj,
                    category=parts.get('category', ''),
                    raw_value=float(parts.get('value', 0)),
                    raw_unit=parts.get('unit', ''),
                    record_date=parts.get('date'),
                    scope=parts.get('scope', 'SCOPE2'),
                    status='PENDING'
                )
                created.append(record.id)
            return Response({"created_ids": created}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='upload/travel')
    def upload_travel(self, request):
        """Accept a JSON file containing travel data and create records."""
        file = request.FILES.get('file')
        if not file:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = json.load(io.BytesIO(file.read()))
            # Expect a list of travel entries with keys matching the model fields
            created = []
            for entry in data:
                company = Company.objects.get(name=entry['company'])
                source_obj, _ = DataSource.objects.get_or_create(company=company, source_type='TRAVEL')
                record = EmissionRecord.objects.create(
                    company=company,
                    source=source_obj,
                    category=entry.get('category', ''),
                    raw_value=float(entry.get('raw_value', 0)),
                    raw_unit=entry.get('raw_unit', ''),
                    record_date=entry.get('record_date'),
                    scope=entry.get('scope', 'SCOPE3'),
                    status='PENDING'
                )
                created.append(record.id)
            return Response({"created_ids": created}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnly ViewSet for AuditLog.
    Enforces immutable security - records can only be viewed, never altered.
    """
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer