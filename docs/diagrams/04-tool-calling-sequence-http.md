# Chat + tool-calling sequence — HTTP/SSE path (Section 6.3)

Regenerated (2026-08-24, Week 5 Phase 1) against the real implementation.
This is a substantial rewrite of the original target, which assumed the
model drives every step via native tool calls (`request_identity_info()`,
`verify_identity()`). The real design (confirmed Week 2, see PROGRESS.md)
is backend-orchestrated: identity collection and verification are
deterministic backend logic plus structured-output extraction calls, never
model-initiated tool calls. **Native Ollama tool-calling is used for exactly
one thing** — `lookup_shipments`, gated to `Verified` sessions only — and
even that is a two-hop round trip (a non-streaming call to get the tool
request, then a separate streaming call for the final prose), not a single
request/response. The transport is HTTP with Server-Sent Events
(`POST /chat/stream`), not the plain request/response Section 6.3 sketched
— WebSocket (6.3b) was never adopted, see `05-tool-calling-sequence-websocket.md`.

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant BE as Backend (gating.py)
    participant Extract as llm/extraction.py +\nintent_classifier.py
    participant Tools as tools/lookup_shipments.py
    participant LLM as Ollama (qwen3:8b)
    participant DB as Postgres

    User->>FE: "Where's my package?"
    FE->>BE: POST /chat/stream {message, session_id}
    BE->>Extract: classify_intent(message)
    Extract->>LLM: chat_json (format: json)
    LLM-->>Extract: {wants_shipment_info: true, ...}
    Extract-->>BE: intent
    Note over BE: state=Anonymous, wants_shipment_info=true —<br/>deterministic template reply, no LLM call for this step
    BE-->>FE: SSE "done": "I need to verify who you are —<br/>name, address, phone?"

    User->>FE: provides name, address, phone
    FE->>BE: POST /chat/stream {message, session_id}
    BE->>Extract: extract_identity_fields(transcript)
    Extract->>LLM: chat_json (format: json)
    LLM-->>Extract: {first_name, last_name, phone_number, address}
    Extract-->>BE: fields (all 4 present)
    BE->>DB: verify_identity() — exact match on\nnormalized name+phone+address
    DB-->>BE: Customer row matched
    BE->>BE: send_verification_code()<br/>(mock SMS, console log only)
    BE->>BE: state=AwaitingCode
    BE-->>FE: SSE "done": "code sent" + state
    FE->>User: shows 6-digit code modal

    User->>FE: enters code
    FE->>BE: POST /verify-code {code, session_id}
    BE->>BE: check_verification_code()<br/>(compare, check expiry/attempts)
    Note over BE: MAX_ATTEMPTS=3, CODE_TTL=10min<br/>(confirmed as-is, Week 5 Phase 0)
    BE->>BE: state=Verified,<br/>customer_id = pending_customer_id
    BE-->>FE: 200 {verified: true, state: "verified"}

    User->>FE: "what's the status of my shipment?"
    FE->>BE: POST /chat/stream {message, session_id}
    Note over BE: state=Verified, customer_id set —<br/>enters _tool_backed_reply_stream (two hops)
    BE->>LLM: HOP 1 — chat_with_tools()<br/>(non-streaming, tool def attached)
    LLM-->>BE: tool_call: lookup_shipments({status?, tracking_number?})
    Note over BE,Tools: Epic F enforcement point:<br/>customer_id ALWAYS comes from<br/>session.customer_id, never from<br/>tool_call arguments — any smuggled<br/>id-shaped key is silently dropped
    BE->>Tools: lookup_shipments(db, session.customer_id, **safe_kwargs)
    Tools->>DB: SELECT * FROM shipments<br/>WHERE customer_id = session.customer_id
    DB-->>Tools: shipment rows (+ packages)
    Tools-->>BE: results (re-queried unfiltered if a\nguessed filter matched nothing)
    BE->>LLM: HOP 2 — chat_stream() with tool result appended
    LLM-->>BE: token, token, token... (streamed)
    BE-->>FE: SSE "token" events, then "done"
    FE->>User: "Your shipment is out for delivery..."
```
