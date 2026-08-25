# Human escalation sequence (Epic G — cosmetic, scripted)

Regenerated (2026-08-24, Week 5 Phase 1) against `backend/gating.py`'s
`_handle_escalation_trigger`/`_handle_escalated_chat` and
`frontend/src/components/ChatWindow/ChatWindow.js`. Two corrections from
the original target: the staged reveal is driven by the frontend splitting
the backend's `\n\n`-separated reply into paragraphs and revealing each with
a 700ms/350ms delay (not a single "color shift" event), and the chat header
bar transitions color and its title changes to "SecureShip — Live Agent" —
it doesn't repaint the whole window. Also, unlike the original target,
nothing in the real state machine ever transitions back out of
`EscalatedToHuman` — see `02-conversation-state-machine.md`'s note.

```mermaid
stateDiagram-v2
    state "Anonymous / CollectingIdentity /\nIdentityRejected / CodeExpired (6.2)" as Unverified
    state "Verified (6.2)" as Ver

    Unverified --> EscalationRequested: "talk to a human"\n(classify_intent: wants_human)
    Ver --> EscalationRequested: "talk to a human"

    EscalationRequested --> ScriptedHandoff: _handle_escalation_trigger()\nsets state=escalated_to_human

    state ScriptedHandoff {
        [*] --> Acknowledging: "Thank you for your patience,\nswitching you to a human"
        Acknowledging --> HumanJoined: "Melany has entered the chat"
        HumanJoined --> ReadingUp: "Hello, my name is Melany,\nlet me just read through the chat..."
        ReadingUp --> Greeting: "Hey [first_name if known],\nI'm up to speed, how can I help?"
        Greeting --> [*]
    }

    note right of ScriptedHandoff
        Frontend reveals each \n\n-separated
        paragraph as its own message bubble
        (700ms delay, 350ms between), and the
        header bar color/title transition to
        "SecureShip — Live Agent" for the
        duration of EscalatedToHuman.
    end note

    ScriptedHandoff --> EscalatedIfUnverified: if escalated while never verified
    ScriptedHandoff --> EscalatedIfVerified: if escalated after verifying

    state EscalatedIfUnverified {
        [*] --> GuardedReply: Roleplays Melany, but stays on the\ntool-less guarded path — same\ndisclosure-scanning backstop as\nany other unverified branch (Epic G4:\nescalation is not a verification bypass)
    }
    state EscalatedIfVerified {
        [*] --> ToolBackedReply: Roleplays Melany, but keeps real\nlookup_shipments access — Epic G4\nonly bars using escalation as a\nbackdoor for someone never verified,\nnot downgrading an already-verified\ncustomer (design call, 2026-08-10)
    }

    note right of EscalatedIfUnverified
        Entirely cosmetic UI theater. No real
        human, no ticketing system. Once here,
        the session stays in EscalatedToHuman
        indefinitely — no code path returns it
        to Anonymous/Verified routing.
    end note
```
