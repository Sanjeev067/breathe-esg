# Data Source Research & Mapping (SOURCES.md)

This document details our research into the real-world operational formats of the three enterprise data sources (SAP, Utility Portals, and Concur Travel) and maps how they translate into our core ledger.

---

## 1. SAP (Fuel and Procurement Data)
*   **Real-World Ingestion Format**: SAP OData services (REST API) or BAPI database queries.
*   **What we learned**: SAP material procurement logs track raw purchases (such as stationary diesel or emergency generator fuel) using plant codes (e.g., `DE_PLANT_40`) and financial codes (GL accounts). The data is often dirty, containing raw metric units (like `Liters`) in Europe and US customary units (like `Gallons`) in North America.
*   **Prototype Mapping**: 
    *   Ingested rows are marked as source `SAP`.
    *   Mapped directly to **Scope 1 (Direct Emissions)**.
    *   Support both standard `Liters` (factor 2.3) and `Gallons` (factor 8.7) automatically converting them to `kg CO2e` normalized values.
*   **What would break in production**: In a live deployment, SAP plant codes must be mapped against an active facility master table to resolve the physical location and local timezone of the plant.

---

## 2. Utility Data (Electricity bills)
*   **Real-World Ingestion Format**: Structured Utility Portal CSV exports or Smart Meter API logs.
*   **What we learned**: Energy portals dump monthly billing logs. Unlike other data, electricity billing periods rarely align with calendar months (e.g., billing from Jan 12 to Feb 14).
*   **Prototype Mapping**:
    *   Ingested rows are marked as source `UTILITY`.
    *   Mapped directly to **Scope 2 (Indirect Emissions)**.
    *   Supports `kWh` (factor 0.4) and `MWh` (factor 400.0) converting them to `kg CO2e`.
*   **What would break in production**: Production requires calendarization algorithms to split overlapping billing cycles into neat monthly buckets (e.g., allocating a Jan 12 - Feb 14 bill proportionally into Jan and Feb emissions).

---

## 3. Corporate Travel (Flights, Hotels, Transport)
*   **Real-World Ingestion Format**: Navan / Concur Travel booking API (JSON payload).
*   **What we learned**: Travel booking systems emit rich booking records. Some travel logs provide the absolute flight distance (in `km` or `miles`), while others only emit airport origin/destination codes (e.g. `JFK-LHR`) requiring geospatial calculations.
*   **Prototype Mapping**:
    *   Ingested rows are marked as source `TRAVEL`.
    *   Mapped directly to **Scope 3 (Other Indirect)**.
    *   Supports distances in `km` (factor 0.15) and `miles` (factor 0.24) automatically converting them to `kg CO2e`.
*   **What would break in production**: Flights need to distinguish between passenger seating classes (Economy vs. First Class) because first-class passengers have a significantly higher carbon footprint allocation per mile.
