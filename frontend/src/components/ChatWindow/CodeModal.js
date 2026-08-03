import { useState } from 'react';
import { useVerifyCode } from '../../api/generated/secureship';

// Rendered on demand only when ChatWindow's session state is
// "awaiting_code" (Epic C2) — never pre-rendered on page load.
function CodeModal({ sessionId, onVerified, onGiveUp }) {
  const [code, setCode] = useState('');
  const [error, setError] = useState(null);
  const { mutateAsync: verifyCode, isPending } = useVerifyCode();

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);

    const result = await verifyCode({ data: { session_id: sessionId, code } });
    if (result.status !== 200) {
      setError('Something went wrong reaching the backend — try again.');
      return;
    }

    const { verified, state, message } = result.data;
    if (verified) {
      onVerified(message);
      return;
    }
    if (state === 'code_expired') {
      onGiveUp(message);
      return;
    }
    // Still "awaiting_code" — wrong code, retry in place.
    setError(message);
    setCode('');
  }

  return (
    <div className="absolute inset-0 z-10 flex items-center justify-center bg-saul-black/70 p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-xs rounded-sm border-2 border-saul-black bg-saul-cream p-5 shadow-2xl"
      >
        <h2 className="font-display text-2xl tracking-wide text-saul-black">
          Verification Code
        </h2>
        <p className="mt-1 font-typewriter text-xs text-saul-black/70">
          We sent a 6-digit code to the phone number on file. Check the
          backend console — this is a mocked SMS, not a real one.
        </p>
        <input
          type="text"
          inputMode="numeric"
          autoFocus
          maxLength={6}
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
          placeholder="000000"
          className="mt-4 w-full rounded-sm border border-saul-black/30 bg-white px-4 py-2 text-center font-display text-2xl tracking-[0.5em] text-saul-black outline-none focus:border-saul-teal"
        />
        {error && (
          <p className="mt-2 font-typewriter text-xs text-saul-rust">{error}</p>
        )}
        <button
          type="submit"
          disabled={isPending || code.length !== 6}
          className="mt-4 w-full rounded-sm bg-saul-rust px-4 py-2 font-display text-lg tracking-wide text-saul-cream disabled:opacity-40"
        >
          {isPending ? 'Checking…' : 'Verify'}
        </button>
      </form>
    </div>
  );
}

export default CodeModal;
