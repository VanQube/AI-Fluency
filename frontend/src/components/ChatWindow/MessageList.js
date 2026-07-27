import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="rounded-sm border border-saul-black/20 bg-saul-mustard/60 px-4 py-2 font-typewriter text-sm text-saul-black">
        <span className="animate-pulse">Building your case…</span>
      </div>
    </div>
  );
}

function MessageList({ messages, isAssistantTyping }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isAssistantTyping]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {isAssistantTyping && <TypingIndicator />}
      <div ref={endRef} />
    </div>
  );
}

export default MessageList;
