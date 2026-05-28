# Architectural Decisions (DECISIONS.md)

This document lists the architectural ambiguities resolved during the development of the prototype, the logic behind our decisions, and outstanding questions for the Product Manager.

---

## 1. Resolved Ambiguities

### A. Data Ingestion Mode: REST API Push
*   **Ambiguity**: The prompt asked to choose an ingestion mechanism (file uploads, API pulls, or manual pastes) for the three sources.
*   **Decision**: We chose to implement standard REST API endpoints (`POST /api/records/` and `POST /api/sources/`).
*   **Justification**: For enterprise architectures (SAP, Utility Portals, Concur), custom point-to-point batch files (CSV/JSON) are best handled by external scripts pushing to a central REST API. This decouples the ingestion pipelines from our core ledger and enables secure real-time programmatic integrations.

### B. ESG Normalization (GHG Protocol Factors)
*   **Ambiguity**: How to map raw units from disparate systems into a single comparable unit of CO2 equivalent.
*   **Decision**: We standardized all outputs into **`kg CO2e`** using established GHG Protocol / EPA conversion factors:
    *   **Scope 1 (Direct Fuel/Gas):** Liters (×2.3), Gallons (×8.7), kg (×3.0).
    *   **Scope 2 (Electricity Grid):** kWh (×0.4), MWh (×400.0).
    *   **Scope 3 (Business Travel):** km (×0.15), miles (×0.24), kg (×0.5).
*   **Justification**: Using a standardized backend utility (`normalize_emission`) ensures that aggregate charts reflect accurate, normalized math regardless of whether data was pushed as Liters or Gallons.

### C. Compliance & Locking Sequence
*   **Ambiguity**: When is a record locked for audit? Is it manual or automatic?
*   **Decision**: We implemented an **Automatic Locking Rule**. When an analyst marks a record's status as `APPROVED`, the database automatically sets `is_locked = True`.
*   **Justification**: Once data is marked as "Approved for Audit", regulatory standards require it to be immutable. Combining approval with database-level locking prevents human tampering post-approval.

---

## 2. Realistic Scope of Ingested Sources

We restricted our prototype ingestion to handle realistic, standard enterprise slices:
1.  **SAP (Fuel/Procurement)**: We focus on stationary diesel, generator fuel, and logistics fuel exports, mapped to **Scope 1** with units like Liters or Gallons.
2.  **Utility Data (Electricity)**: We map billing period consumption values (kWh or MWh) directly to **Scope 2**.
3.  **Corporate Travel (Concur/Navan)**: We map employee travel distances (km or miles) from flights and ground transport directly to **Scope 3**.

---

## 3. Outstanding Questions for the PM

If we could align with the Product Manager, we would clarify:
1.  **Custom Grid Emission Factors**: Should Scope 2 calculations query a local grid API (e.g., eGRID in the US) to adjust factors dynamically based on zip codes/plant locations?
2.  **Concur Distance Calculator**: For travel records that only provide origin/destination airport codes (e.g., JFK to LHR), should the backend integrate a Great-Circle distance API to calculate passenger kilometers automatically?
3.  **ERP Master Data Synced Lookups**: Should plant codes found in SAP be cross-referenced with a master database table in Django to resolve them into company locations and physical addresses?
