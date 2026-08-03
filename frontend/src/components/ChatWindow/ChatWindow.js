import { useState } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import CodeModal from './CodeModal';
import { streamChatMessage } from '../../api/chatStream';

function makeId() {
  return crypto.randomUUID();
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const WELCOME_MESSAGE = {
  id: makeId(),
  role: 'assistant',
  content:
    "Well hello there! Name's not Saul, but I'll fight for your package just " +
    "as hard. Tell me about your shipment — this call may be recorded for " +
    'quality assurance (it is not, but doesn’t that sound official).',
  timestamp: new Date().toISOString(),
};

// Below this many buffered chunks we can't yet tell a real token-by-token
// LLM stream apart from a deterministic reply that arrived as one chunk
// (Epic G's escalation script, "thanks I've sent a code", etc.) — wait for
// a second chunk (or the stream ending) before deciding how to render it,
// so a one-shot reply never flashes on screen before being replaced.
const STREAMING_CONFIRMED_AT = 2;

function ChatWindow() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [sessionId, setSessionId] = useState(null);
  const [sessionState, setSessionState] = useState('anonymous');
  const [isBusy, setIsBusy] = useState(false);
  const [isWaitingForFirstToken, setIsWaitingForFirstToken] = useState(false);
  const [isStaging, setIsStaging] = useState(false);

  function addMessage(role, content, timestamp) {
    const id = makeId();
    setMessages((prev) => [
      ...prev,
      { id, role, content, timestamp: timestamp ?? new Date().toISOString() },
    ]);
    return id;
  }

  function updateMessageContent(id, content) {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, content } : m)));
  }

  // Epic G2's "scripted, timed sequence": reveal the backend's paragraph-
  // separated escalation reply one piece at a time instead of dumping it
  // all at once — there's no WebSocket server-push (Section 6.3, not 6.3b)
  // to do this from the backend side.
  async function revealEscalationSequence(replyText) {
    const stages = replyText.split('\n\n').filter(Boolean);
    for (const stage of stages) {
      setIsStaging(true);
      await delay(700);
      setIsStaging(false);
      addMessage('assistant', stage);
      await delay(350);
    }
  }

  async function handleSend(text) {
    addMessage('user', text);
    setIsBusy(true);
    setIsWaitingForFirstToken(true);

    let assistantId = null;
    let accumulated = '';
    let chunkCount = 0;
    let finalEvent = null;

    try {
      for await (const event of streamChatMessage({ session_id: sessionId, message: text })) {
        if (event.type === 'error') {
          throw new Error('stream error');
        }
        if (event.type === 'token') {
          accumulated += event.content;
          chunkCount += 1;
          if (chunkCount === STREAMING_CONFIRMED_AT) {
            setIsWaitingForFirstToken(false);
            assistantId = addMessage('assistant', accumulated);
          } else if (assistantId) {
            updateMessageContent(assistantId, accumulated);
          }
        } else if (event.type === 'done') {
          finalEvent = event;
        }
      }
    } catch (err) {
      setIsBusy(false);
      setIsWaitingForFirstToken(false);
      addMessage(
        'assistant',
        'Objection — connection trouble! Check that the backend and Ollama are running, counselor.'
      );
      return;
    }

    setIsWaitingForFirstToken(false);

    if (finalEvent) {
      setSessionId(finalEvent.session_id);
      const justEscalated =
        finalEvent.state === 'escalated_to_human' && sessionState !== 'escalated_to_human';
      setSessionState(finalEvent.state);

      if (!assistantId) {
        // Never confirmed a real multi-chunk stream — one-shot deterministic
        // reply (or the escalation script), decide how to show it now.
        if (justEscalated) {
          await revealEscalationSequence(finalEvent.reply ?? accumulated);
        } else {
          addMessage('assistant', finalEvent.reply ?? accumulated);
        }
      }
      // else: a real token stream already rendered progressively in place.
    }

    setIsBusy(false);
  }

  const escalated = sessionState === 'escalated_to_human';

  return (
    <div className="relative flex h-[600px] w-full max-w-md flex-col rounded-sm border-2 border-saul-black bg-saul-cream shadow-2xl">
      <div
        className={`px-4 py-3 transition-colors duration-700 ${
          escalated
            ? 'bg-gradient-to-r from-saul-teal to-saul-black'
            : 'bg-gradient-to-r from-saul-rust to-saul-orange'
        }`}
      >
        <h1 className="font-display text-2xl tracking-wide text-saul-cream">
          {escalated ? 'SecureShip — Live Agent' : 'SecureShip Legal & Logistics'}
        </h1>
        <p className="font-typewriter text-xs italic text-saul-cream/80">
          {escalated
            ? "You're through to a (theatrical) human. Still playing by the rules."
            : 'Se habla shipping. Local model, no billable hours.'}
        </p>
      </div>
      <MessageList messages={messages} isAssistantTyping={isWaitingForFirstToken || isStaging} />
      <MessageInput onSend={handleSend} disabled={isBusy} />
      {sessionState === 'awaiting_code' && (
        <CodeModal
          sessionId={sessionId}
          onVerified={(message) => {
            setSessionState('verified');
            addMessage('assistant', message);
          }}
          onGiveUp={(message) => {
            setSessionState('code_expired');
            addMessage('assistant', message);
          }}
        />
      )}
    </div>
  );
}

export default ChatWindow;
