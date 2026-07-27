import { useState } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { useSendChatMessage } from '../../api/generated/secureship';

function makeId() {
  return crypto.randomUUID();
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

function ChatWindow() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [sessionId, setSessionId] = useState(null);
  const { mutateAsync: sendChatMessage, isPending } = useSendChatMessage();

  async function handleSend(text) {
    const userMessage = {
      id: makeId(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    const result = await sendChatMessage({
      data: { session_id: sessionId, message: text },
    });

    if (result.status !== 200) {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: 'assistant',
          content:
            "Objection — connection trouble! Check that the backend and Ollama are running, counselor.",
          timestamp: new Date().toISOString(),
        },
      ]);
      return;
    }

    setSessionId(result.data.session_id);
    setMessages((prev) => [
      ...prev,
      {
        id: makeId(),
        role: 'assistant',
        content: result.data.reply,
        timestamp: result.data.timestamp,
      },
    ]);
  }

  return (
    <div className="flex h-[600px] w-full max-w-md flex-col rounded-sm border-2 border-saul-black bg-saul-cream shadow-2xl">
      <div className="bg-gradient-to-r from-saul-rust to-saul-orange px-4 py-3">
        <h1 className="font-display text-2xl tracking-wide text-saul-cream">
          SecureShip Legal &amp; Logistics
        </h1>
        <p className="font-typewriter text-xs italic text-saul-cream/80">
          Se habla shipping. Local model, no billable hours.
        </p>
      </div>
      <MessageList messages={messages} isAssistantTyping={isPending} />
      <MessageInput onSend={handleSend} disabled={isPending} />
    </div>
  );
}

export default ChatWindow;
