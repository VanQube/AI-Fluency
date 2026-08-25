# Conversation / identity-gating state machine

Regenerated (2026-08-24, Week 5 Phase 1) against the real implementation in
`backend/gating.py` and `backend/models/chat_session.py`. Backend-orchestrated,
not model-driven: the LLM only phrases replies and extracts fields via
structured output (`llm/extraction.py`, `llm/intent_classifier.py`) — every
transition below is decided deterministically in `gating.py`, never by the
model choosing to call a tool. The `CodeSent` state from the original target
diagram is still defined in `SESSION_STATES` and handled defensively
alongside `AwaitingCode` by the router, but nothing in `gating.py` actually
assigns it — `CollectingIdentity` goes straight to `AwaitingCode`.

```mermaid
stateDiagram-v2
    [*] --> Anonymous

    Anonymous --> Anonymous: General chat (guarded reply —\nno shipment claims allowed)
    Anonymous --> CollectingIdentity: Shipment question OR\nunprompted identity info
    Anonymous --> EscalatedToHuman: "talk to a human"\n(checked first, from any state)

    CollectingIdentity --> CollectingIdentity: Fields still missing
    CollectingIdentity --> IdentityRejected: All 4 fields given,\nno Customer match
    CollectingIdentity --> AwaitingCode: Match found —\ncode sent immediately

    IdentityRejected --> CollectingIdentity: Retries with new info
    IdentityRejected --> Anonymous: Gives up\n(no new info on repeat miss)

    AwaitingCode --> AwaitingCode: Wrong code (attempt < 3)\nor non-code chat message
    AwaitingCode --> Verified: Correct code
    AwaitingCode --> CodeExpired: 3 wrong attempts\nOR 10-min TTL elapsed

    CodeExpired --> Anonymous: Message doesn't volunteer\nidentity info — give up (fixed\nWeek 5 Phase 3, see below)
    CodeExpired --> CollectingIdentity: Message volunteers identity\ninfo — re-extract + re-verify\n(e.g. retrying with a fresh code)
    note right of CodeExpired
        Fixed 2026-08-24 (Week 5 Phase 3): previously
        collected_fields was still fully populated from
        the earlier match, so ANY message here — including
        "never mind, different question" — silently
        re-verified and sent a new code. Now gated on the
        turn's classify_intent() signal the same way
        IdentityRejected already was, before re-running
        extraction. Verified live: give-up now correctly
        drops to Anonymous; re-stating identity still
        correctly resends a fresh code.
    end note

    Verified --> Verified: lookup_shipments scoped to\nsession.customer_id ONLY (Epic F)
    Verified --> EscalatedToHuman: "talk to a human" —\nkeeps real tool access (Epic G4)

    EscalatedToHuman --> EscalatedToHuman: Stays in "Melany" persona\nindefinitely — tool-backed if\ncustomer_id was set, guarded\n(tool-less) otherwise. No code\npath returns to Anonymous/Verified\nrouting once escalated.
```
