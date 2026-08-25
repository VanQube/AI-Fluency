# Tool-calling sequence — WebSocket path (Section 6.3b, optional upgrade)

**Status as of Week 5 (2026-08-24): not adopted.** The team went with HTTP +
Server-Sent Events instead (`POST /chat/stream`, see the real, implemented
sequence in `04-tool-calling-sequence-http.md`) — SSE covered the actual
requirement (token-by-token streaming for perceived latency, Section 8's
Week 2 follow-up) without a second transport to maintain. This file is kept
as an unbuilt reference only; the sequence below was never updated against
real code because there is no real code behind it, and the message shapes
below (`emit "message"`, `emit "verified"`, etc.) reflect the original
target design, not any live wire protocol. The one idea worth remembering
if this is ever revisited: the note at the bottom about push-based
`shipment_updated` notifications is a genuine capability gap in the current
HTTP/SSE build — an admin edit only shows up in an open chat on the
customer's *next* message, not live.

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant WS as Backend (WebSocket Gateway)
    participant Session as Session Store
    participant LLM as Local LLM (Ollama)
    participant Tools as Tool Layer
    participant DB as Database

    FE->>WS: connect (ws://.../chat?session_id=...)
    WS-->>FE: connection established

    User->>FE: "Where's my package?"
    FE->>WS: emit "message" {text}
    WS->>FE: emit "typing" (assistant is "typing")
    WS->>Session: get session state
    Session-->>WS: state = "Anonymous"
    WS->>LLM: prompt + tool defs + state context
    LLM-->>WS: tool_call: request_identity_info()
    WS->>FE: emit "message" (assistant asks for name/address/phone)

    User->>FE: provides name, address, phone
    FE->>WS: emit "message" {text}
    WS->>LLM: prompt with collected fields
    LLM-->>WS: tool_call: verify_identity(fields)
    WS->>Tools: verify_identity(fields)
    Tools->>DB: match against Customer table
    DB-->>Tools: match found: customer_id=123
    Tools->>Session: set pending_customer_id=123, state="CodeSent"
    Tools-->>WS: result: code sent (mocked)
    WS->>FE: emit "show_code_modal"  Note: pushed, not polled
    FE->>User: shows 6-digit code modal

    User->>FE: enters code
    FE->>WS: emit "verify_code" {code}
    WS->>Tools: check_verification_code(code, session_id)
    Tools->>Session: compare code, check expiry/attempts
    Session-->>Tools: match, not expired
    Tools->>Session: set state="Verified", customer_id=123
    Tools-->>WS: verified = true
    WS->>FE: emit "verified" (chat unlocked, no page reload needed)

    Note over WS,DB: Same enforcement point as HTTP path:<br/>Tools layer ALWAYS uses session.customer_id,<br/>never a model/user-supplied id.<br/>Transport changed; gating contract did not.

    User->>FE: "What's the status of my shipment?"
    FE->>WS: emit "message" {text}
    WS->>Tools: lookup_shipments(customer_id=123)
    Tools->>DB: SELECT * FROM shipments WHERE customer_id=123
    DB-->>Tools: shipment rows
    Tools-->>WS: shipment data
    WS->>LLM: tool result
    LLM-->>WS: natural-language answer
    WS->>FE: emit "message" (assistant reply)

    Note over WS,FE: Bonus real-time win (HTTP can't do this easily):<br/>if an admin edits this shipment right now,<br/>the backend can emit "shipment_updated" and<br/>the open chat reflects it without a refresh.
```
