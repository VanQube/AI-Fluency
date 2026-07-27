import { useState } from 'react';

function MessageInput({ onSend, disabled }) {
  const [value, setValue] = useState('');

  function handleSubmit(event) {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 border-t-2 border-saul-black bg-saul-cream p-3">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Describe your shipping situation, counselor…"
        disabled={disabled}
        className="flex-1 rounded-sm border border-saul-black/30 bg-white px-4 py-2 font-typewriter text-sm text-saul-black outline-none focus:border-saul-teal disabled:bg-saul-cream"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="rounded-sm bg-saul-rust px-4 py-2 font-display text-lg tracking-wide text-saul-cream disabled:opacity-40"
      >
        File It
      </button>
    </form>
  );
}

export default MessageInput;
