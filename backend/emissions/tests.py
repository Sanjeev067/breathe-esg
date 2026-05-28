from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
import datetime

from .models import Company, DataSource, EmissionRecord, AuditLog
from .utils import normalize_emission


class UnitConversionTestCase(TestCase):
    """
    Test cases to verify raw-to-normalized emissions unit conversions.
    """
    def test_scope1_conversions(self):
        # Liters: 2.3 kg CO2e / liter
        val, unit = normalize_emission("SCOPE1", 100, "Liters")
        self.assertEqual(val, 230.0)
        self.assertEqual(unit, "kg CO2e")

        # Gallons: 8.7 kg CO2e / gallon
        val, unit = normalize_emission("SCOPE1", 10, "Gallons")
        self.assertEqual(val, 87.0)

        # kg: 3.0 kg CO2e / kg
        val, unit = normalize_emission("SCOPE1", 50, "kg")
        self.assertEqual(val, 150.0)

    def test_scope2_conversions(self):
        # kWh: 0.4 kg CO2e / kWh
        val, unit = normalize_emission("SCOPE2", 1000, "kWh")
        self.assertEqual(val, 400.0)

        # MWh: 400.0 kg CO2e / MWh
        val, unit = normalize_emission("SCOPE2", 5, "MWh")
        self.assertEqual(val, 2000.0)

    def test_scope3_conversions(self):
        # km: 0.15 kg CO2e / km
        val, unit = normalize_emission("SCOPE3", 1000, "km")
        self.assertEqual(val, 150.0)

        # miles: 0.24 kg CO2e / mile
        val, unit = normalize_emission("SCOPE3", 100, "miles")
        self.assertEqual(val, 24.0)

    def test_fallback_conversions(self):
        # Unknown unit should default to 1.0 factor
        val, unit = normalize_emission("SCOPE1", 100, "widgets")
        self.assertEqual(val, 100.0)


class EmissionRecordModelTestCase(TestCase):
    """
    Test cases verifying model-level validation, multi-tenant checks, and record-locking.
    """
    def setUp(self):
        self.company1 = Company.objects.create(name="Company A", industry="Tech")
        self.company2 = Company.objects.create(name="Company B", industry="Retail")
        self.source1 = DataSource.objects.create(company=self.company1, source_type="UTILITY")
        self.source2 = DataSource.objects.create(company=self.company2, source_type="UTILITY")

    def test_valid_record_creation(self):
        record = EmissionRecord.objects.create(
            company=self.company1,
            source=self.source1,
            category="Electricity",
            raw_value=1500,
            raw_unit="kWh",
            record_date=datetime.date(2026, 5, 1),
            scope="SCOPE2"
        )
        self.assertEqual(record.normalized_value, 600.0)
        self.assertEqual(record.status, "PENDING")
        self.assertEqual(record.is_locked, False)

        # Confirm CREATED audit log was generated
        log = AuditLog.objects.filter(record=record, action="CREATED").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.new_value, 1500)

    def test_company_mismatch_raises_validation_error(self):
        # Mismatch source1 (Company A) with Company B
        record = EmissionRecord(
            company=self.company2,
            source=self.source1,
            category="Electricity",
            raw_value=1500,
            raw_unit="kWh",
            record_date=datetime.date(2026, 5, 1),
            scope="SCOPE2"
        )
        with self.assertRaises(ValidationError):
            record.save()

    def test_negative_value_raises_validation_error(self):
        record = EmissionRecord(
            company=self.company1,
            source=self.source1,
            category="Electricity",
            raw_value=-50,
            raw_unit="kWh",
            record_date=datetime.date(2026, 5, 1),
            scope="SCOPE2"
        )
        with self.assertRaises(ValidationError):
            record.save()

    def test_record_locking_on_approve(self):
        record = EmissionRecord.objects.create(
            company=self.company1,
            source=self.source1,
            category="Electricity",
            raw_value=100,
            raw_unit="kWh",
            record_date=datetime.date(2026, 5, 1),
            scope="SCOPE2"
        )
        self.assertFalse(record.is_locked)

        # Approve should lock
        record.status = "APPROVED"
        record.save()
        self.assertTrue(record.is_locked)

        # Attempt to edit locked record should raise ValidationError
        record.raw_value = 200
        with self.assertRaises(ValidationError):
            record.save()

        # Attempt to delete locked record should raise ValidationError
        with self.assertRaises(ValidationError):
            record.delete()

    def test_audit_logging_value_updates(self):
        record = EmissionRecord.objects.create(
            company=self.company1,
            source=self.source1,
            category="Electricity",
            raw_value=100,
            raw_unit="kWh",
            record_date=datetime.date(2026, 5, 1),
            scope="SCOPE2"
        )
        # Edit value
        record.raw_value = 150
        record.save()

        # Check UPDATED audit log
        log = AuditLog.objects.filter(record=record, action="UPDATED").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.old_value, 100)
        self.assertEqual(log.new_value, 150)


class EmissionRecordAPITestCase(APITestCase):
    """
    Test cases to verify REST API endpoints, security validation, and analytics.
    """
    def setUp(self):
        self.company = Company.objects.create(name="Tesla Corp", industry="Automotive")
        self.source = DataSource.objects.create(company=self.company, source_type="UTILITY")

        # Seed records for API testing
        self.record1 = EmissionRecord.objects.create(
            company=self.company,
            source=self.source,
            category="Gigafactory Power",
            raw_value=5000.0,
            raw_unit="kWh",
            record_date=datetime.date(2026, 3, 1),
            scope="SCOPE2",
            status="PENDING"
        )

        self.record2 = EmissionRecord.objects.create(
            company=self.company,
            source=self.source,
            category="Supercharger Grid",
            raw_value=8000.0,
            raw_unit="kWh",
            record_date=datetime.date(2026, 4, 1),
            scope="SCOPE2",
            status="PENDING"
        )

    def test_list_records(self):
        response = self.client.get('/api/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_record_via_api(self):
        data = {
            "company": self.company.id,
            "source": self.source.id,
            "category": "Office AC",
            "raw_value": 3000.0,
            "raw_unit": "kWh",
            "record_date": "2026-05-01",
            "scope": "SCOPE2",
            "status": "PENDING"
        }
        response = self.client.post('/api/records/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["normalized_value"], 1200.0) # 3000 * 0.4
        self.assertEqual(response.data["normalized_unit"], "kg CO2e")

    def test_approve_endpoint(self):
        url = f'/api/records/{self.record1.id}/approve/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "APPROVED")
        self.assertEqual(response.data["is_locked"], True)

        # Check that it is now locked in DB
        self.record1.refresh_from_db()
        self.assertTrue(self.record1.is_locked)

    def test_reject_endpoint(self):
        url = f'/api/records/{self.record1.id}/reject/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "REJECTED")
        self.assertEqual(response.data["is_locked"], False)

    def test_analytics_endpoint(self):
        response = self.client.get('/api/records/analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Aggregated values check
        # Record 1 (5000 kWh -> 2000 kg CO2e) + Record 2 (8000 kWh -> 3200 kg CO2e) = 5200 kg CO2e
        self.assertEqual(response.data["total_all"], 5200.0)
        self.assertIn("SCOPE2", response.data["by_scope"])
        self.assertEqual(response.data["by_scope"]["SCOPE2"], 5200.0)
        self.assertEqual(len(response.data["monthly_trends"]), 2)
