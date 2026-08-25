# Data model (ERD)

Regenerated (2026-08-24, Week 5 Phase 1) against the real SQLAlchemy models
in `backend/models/`. Two changes from the original target diagram:
`CHAT_SESSION` carries several fields the spec's high-level sketch omitted
(they're what actually implements Section 6.2's state machine), and
`ADMIN_USER` is gone entirely — per the Week 4 design call (confirmed
2026-08-24), Auth0 is the sole source of truth for admin identity and no
local table mirrors it, so there's nothing to diagram.

```mermaid
erDiagram
    CUSTOMER ||--o{ SHIPMENT : has
    SHIPMENT ||--o{ PACKAGE : contains
    CUSTOMER ||--o{ CHAT_SESSION : "may be linked to (post-verification)"
    CUSTOMER {
        uuid id PK
        string first_name
        string last_name
        string phone_number
        string address
    }
    SHIPMENT {
        uuid id PK
        uuid customer_id FK
        string tracking_number
        string status "label_created | in_transit |\nout_for_delivery | delivered |\nexception (plain string, no DB enum)"
        string carrier
        string origin
        string destination
        date estimated_delivery
        datetime last_update
    }
    PACKAGE {
        uuid id PK
        uuid shipment_id FK
        string description
        decimal weight_kg
        decimal declared_value
    }
    CHAT_SESSION {
        uuid id PK
        uuid customer_id FK "nullable — set ONCE, only on\nsuccessful code verification (Epic F's\nenforcement signal, independent of\nwhat state displays afterward)"
        uuid pending_customer_id FK "nullable — candidate match while\nawaiting code, promoted to\ncustomer_id on success"
        string state "anonymous | collecting_identity |\nidentity_rejected | code_sent* |\nawaiting_code | code_expired |\nverified | escalated_to_human\n(*defined, currently unreachable)"
        jsonb collected_fields "first_name/last_name/phone_number/\naddress, filled in incrementally"
        string verification_code "nullable, cleared after use"
        datetime code_expires_at "nullable, 10-min TTL"
        int code_attempts "default 0, locks at 3"
        datetime started_at
        datetime ended_at "nullable — not currently set\nanywhere in the app"
        jsonb transcript "array of {role, content, timestamp}"
    }
```

> `ADMIN_USER` is not a table in this schema — see the note above. Admin
> identity is validated per-request against Auth0's JWKS
> (`backend/admin_auth.py`), not looked up locally.
