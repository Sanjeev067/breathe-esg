# Architectural Tradeoffs (TRADEOFFS.md)

To ensure the prototype delivered for the 4-day deadline is extremely robust, secure, and production-ready, we deliberately deferred three complex features. This document explains what was left out and why.

---

## 1. Deferring the React Frontend Setup
*   **What was left out**: Setting up a separate, boilerplate React client codebase.
*   **Why**: Rather than building a shallow, non-functional frontend mockup with generic CRUD screens, we focused our energy on designing a robust, bulletproof Django database engine, unit conversion utility, multi-tenant validations, record locking constraints, automated audit logging, and high-performance SQL analytics. The backend provides a fully functional web browsable interface (via Django REST Framework) which is instantly testable. The React UI can now easily be layered on top as a clean single-page app utilizing this API.

## 2. Deferring Role-Based Access Control (RBAC)
*   **What was left out**: API authentication (JWT/OAuth) and division of user permissions (e.g. distinguishing an "Analyst" who can edit/approve from an "Auditor" who only has read-only permissions).
*   **Why**: Designing enterprise identity management (Active Directory / Okta integrations) requires deep customer-specific security alignments. For this prototype, we built the foundational state machine (status transitions and record locking flags) at the database layer. This ensures that once *any* client approves a record, the ORM locks it permanently, independent of the authentication framework.

## 3. Deferring PDF Invoice OCR Parsing
*   **What was left out**: A document parsing pipeline (using OCR or LLMs) to extract meter readings and dates from raw PDF utility bills.
*   **Why**: Bill parsing is a complex domain prone to layout changes and accuracy issues. In practice, enterprise teams either buy parsed utility data from aggregators (like Urjanet) or pull structured CSV logs from utility portal sweeps. We assumed utility portal CSV sweeps are parsed by an ingestion script before being pushed to our REST API.
