function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] rounded-sm border px-4 py-2 text-sm shadow-sm ${
          isUser
            ? 'border-saul-teal/40 bg-saul-teal text-saul-cream'
            : 'border-saul-black/20 bg-saul-mustard font-typewriter text-saul-black'
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}

export default MessageBubble;
