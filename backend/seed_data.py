import os
import django
import datetime

# 1. Initialize Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from emissions.models import Company, DataSource, EmissionRecord, AuditLog


def seed_database():
    print("Clearing existing data...")
    AuditLog.objects.all().delete()
    EmissionRecord.objects.all().delete()
    DataSource.objects.all().delete()
    Company.objects.all().delete()

    print("Creating Companies...")
    ecocorp = Company.objects.create(name="EcoCorp Solutions", industry="Technology")
    aerogreen = Company.objects.create(name="AeroGreen Logistics", industry="Transport")

    print("Creating Data Sources...")
    # EcoCorp Data Sources
    ec_sap = DataSource.objects.create(company=ecocorp, source_type="SAP")
    ec_utility = DataSource.objects.create(company=ecocorp, source_type="UTILITY")
    ec_travel = DataSource.objects.create(company=ecocorp, source_type="TRAVEL")

    # AeroGreen Data Sources
    ag_sap = DataSource.objects.create(company=aerogreen, source_type="SAP")
    ag_utility = DataSource.objects.create(company=aerogreen, source_type="UTILITY")
    ag_travel = DataSource.objects.create(company=aerogreen, source_type="TRAVEL")

    print("Creating Emission Records...")
    # EcoCorp Records
    records = [
        # EcoCorp Electricity (Scope 2)
        {
            "company": ecocorp,
            "source": ec_utility,
            "category": "Office Electricity",
            "raw_value": 12000.0,
            "raw_unit": "kWh",
            "record_date": datetime.date(2026, 1, 15),
            "scope": "SCOPE2",
            "status": "PENDING"
        },
        {
            "company": ecocorp,
            "source": ec_utility,
            "category": "Office Electricity",
            "raw_value": 14500.0,
            "raw_unit": "kWh",
            "record_date": datetime.date(2026, 2, 15),
            "scope": "SCOPE2",
            "status": "APPROVED" # Will auto-lock
        },
        # EcoCorp Stationary Combustion (Scope 1)
        {
            "company": ecocorp,
            "source": ec_sap,
            "category": "Backup Generators",
            "raw_value": 500.0,
            "raw_unit": "Liters",
            "record_date": datetime.date(2026, 3, 1),
            "scope": "SCOPE1",
            "status": "PENDING"
        },
        # EcoCorp Travel (Scope 3)
        {
            "company": ecocorp,
            "source": ec_travel,
            "category": "Employee Flights",
            "raw_value": 15000.0,
            "raw_unit": "km",
            "record_date": datetime.date(2026, 4, 10),
            "scope": "SCOPE3",
            "status": "APPROVED" # Will auto-lock
        },
        # EcoCorp Mobile Combustion (Scope 1)
        {
            "company": ecocorp,
            "source": ec_sap,
            "category": "Executive Transport Fuel",
            "raw_value": 200.0,
            "raw_unit": "Gallons",
            "record_date": datetime.date(2026, 5, 5),
            "scope": "SCOPE1",
            "status": "FLAGGED"
        },
        # EcoCorp Travel (Scope 3)
        {
            "company": ecocorp,
            "source": ec_travel,
            "category": "Staff Commuting",
            "raw_value": 2500.0,
            "raw_unit": "miles",
            "record_date": datetime.date(2026, 5, 20),
            "scope": "SCOPE3",
            "status": "REJECTED"
        },

        # AeroGreen Records
        # AeroGreen Fleet Diesel (Scope 1)
        {
            "company": aerogreen,
            "source": ag_sap,
            "category": "Truck Fleet Diesel",
            "raw_value": 3500.0,
            "raw_unit": "Gallons",
            "record_date": datetime.date(2026, 1, 10),
            "scope": "SCOPE1",
            "status": "APPROVED"
        },
        {
            "company": aerogreen,
            "source": ag_sap,
            "category": "Truck Fleet Diesel",
            "raw_value": 4000.0,
            "raw_unit": "Gallons",
            "record_date": datetime.date(2026, 2, 12),
            "scope": "SCOPE1",
            "status": "APPROVED"
        },
        # AeroGreen Warehouse Electricity (Scope 2)
        {
            "company": aerogreen,
            "source": ag_utility,
            "category": "Main Warehouse Grid",
            "raw_value": 45000.0,
            "raw_unit": "kWh",
            "record_date": datetime.date(2026, 3, 1),
            "scope": "SCOPE2",
            "status": "APPROVED"
        },
        # AeroGreen Business Travel (Scope 3)
        {
            "company": aerogreen,
            "source": ag_travel,
            "category": "Logistics Route Planning Travel",
            "raw_value": 30000.0,
            "raw_unit": "km",
            "record_date": datetime.date(2026, 3, 15),
            "scope": "SCOPE3",
            "status": "PENDING"
        },
        # AeroGreen Fleet Diesel (Scope 1)
        {
            "company": aerogreen,
            "source": ag_sap,
            "category": "Truck Fleet Diesel",
            "raw_value": 4200.0,
            "raw_unit": "Gallons",
            "record_date": datetime.date(2026, 4, 20),
            "scope": "SCOPE1",
            "status": "PENDING"
        },
        # AeroGreen Warehouse Electricity (Scope 2)
        {
            "company": aerogreen,
            "source": ag_utility,
            "category": "Main Warehouse Grid",
            "raw_value": 48000.0,
            "raw_unit": "kWh",
            "record_date": datetime.date(2026, 5, 1),
            "scope": "SCOPE2",
            "status": "APPROVED"
        }
    ]

    for rec in records:
        record = EmissionRecord.objects.create(
            company=rec["company"],
            source=rec["source"],
            category=rec["category"],
            raw_value=rec["raw_value"],
            raw_unit=rec["raw_unit"],
            record_date=rec["record_date"],
            scope=rec["scope"],
            status=rec["status"]
        )
        print(f"  Created EmissionRecord ID {record.id}: '{record.category}' for {record.company.name}")
        print(f"    Raw Value: {record.raw_value} {record.raw_unit} -> Normalized: {record.normalized_value} {record.normalized_unit} (Locked: {record.is_locked})")

    print("\nDatabase seeded successfully!")
    print(f"Total Companies: {Company.objects.count()}")
    print(f"Total Data Sources: {DataSource.objects.count()}")
    print(f"Total Emission Records: {EmissionRecord.objects.count()}")
    print(f"Total Audit Logs Created: {AuditLog.objects.count()}")


if __name__ == "__main__":
    seed_database()
