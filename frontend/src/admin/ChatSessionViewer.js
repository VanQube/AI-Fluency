import { useState } from 'react';
import { useListChatSessions, useGetChatSession } from '../api/generated/secureship';
import { authFetch } from './authFetch';

// Week 5 stretch goal — read-only admin view of past ChatSession rows and
// their transcripts (Section 4.6's JSONB column). No create/update/delete;
// this only ever displays what gating.py already wrote during real
// conversations. Deliberately surfaces the escalation flag
// (state === "escalated_to_human") and the gating-rejection states
// (identity_rejected, code_expired) as distinct badges, per Section 8's
// Week 5 plan calling those out as the interesting rows to show side by
// side.
const STATE_BADGE_CLASSES = {
  verified: 'bg-saul-teal/20 text-saul-teal border-saul-teal/40',
  escalated_to_human: 'bg-saul-mustard/60 text-saul-black border-saul-black/30',
  identity_rejected: 'bg-saul-rust/20 text-saul-rust border-saul-rust/40',
  code_expired: 'bg-saul-rust/20 text-saul-rust border-saul-rust/40',
};
const DEFAULT_BADGE_CLASSES = 'bg-saul-black/5 text-saul-black/70 border-saul-black/20';

function StateBadge({ state }) {
  return (
    <span
      className={`inline-block rounded-sm border px-2 py-0.5 font-typewriter text-xs ${
        STATE_BADGE_CLASSES[state] ?? DEFAULT_BADGE_CLASSES
      }`}
    >
      {state}
    </span>
  );
}

function formatTimestamp(value) {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

function TranscriptView({ transcript }) {
  if (!transcript || transcript.length === 0) {
    return <p className="font-typewriter text-sm text-saul-black/60">No messages recorded.</p>;
  }
  return (
    <div className="space-y-2">
      {transcript.map((entry, i) => (
        <div
          key={i}
          className={`rounded-sm border px-3 py-2 text-sm font-typewriter ${
            entry.role === 'user'
              ? 'border-saul-teal/30 bg-saul-teal/10'
              : entry.role === 'system'
              ? 'border-saul-black/20 bg-saul-black/5 text-saul-black/60 italic'
              : 'border-saul-mustard/50 bg-saul-mustard/20'
          }`}
        >
          <div className="mb-1 flex items-center justify-between text-xs text-saul-black/50">
            <span className="font-display tracking-wide">{entry.role}</span>
            <span>{formatTimestamp(entry.timestamp)}</span>
          </div>
          <div className="whitespace-pre-wrap">{entry.content}</div>
        </div>
      ))}
    </div>
  );
}

function ChatSessionViewer({ token }) {
  const { data, isLoading } = useListChatSessions({ fetch: authFetch(token) });
  const [selectedId, setSelectedId] = useState(null);
  const { data: detail, isLoading: isLoadingDetail } = useGetChatSession(selectedId, {
    fetch: authFetch(token),
    query: { enabled: selectedId !== null },
  });

  const sessions = data?.data ?? [];

  if (isLoading) {
    return <p className="font-typewriter text-sm text-saul-black/60">Loading…</p>;
  }

  if (sessions.length === 0) {
    return <p className="font-typewriter text-sm text-saul-black/60">No chat sessions yet.</p>;
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="overflow-x-auto rounded-sm border border-saul-black/20">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-saul-black/20 bg-saul-cream">
              <th className="px-3 py-2 font-display text-base tracking-wide text-saul-black">
                Started
              </th>
              <th className="px-3 py-2 font-display text-base tracking-wide text-saul-black">
                State
              </th>
              <th className="px-3 py-2 font-display text-base tracking-wide text-saul-black">
                Customer
              </th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody>
            {sessions.map((session) => (
              <tr
                key={session.id}
                className={`cursor-pointer border-b border-saul-black/10 last:border-0 hover:bg-saul-cream ${
                  selectedId === session.id ? 'bg-saul-cream' : ''
                }`}
                onClick={() => setSelectedId(session.id)}
              >
                <td className="px-3 py-2 font-typewriter text-saul-black/90">
                  {formatTimestamp(session.started_at)}
                </td>
                <td className="px-3 py-2">
                  <StateBadge state={session.state} />
                </td>
                <td className="px-3 py-2 font-typewriter text-saul-black/70">
                  {session.customer_id ? session.customer_id.slice(0, 8) : '— unverified —'}
                </td>
                <td className="px-3 py-2 text-right">
                  <button
                    type="button"
                    onClick={() => setSelectedId(session.id)}
                    className="text-xs font-typewriter text-saul-teal underline"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="rounded-sm border border-saul-black/20 bg-white p-4">
        {!selectedId && (
          <p className="font-typewriter text-sm text-saul-black/60">
            Select a session to view its transcript.
          </p>
        )}
        {selectedId && isLoadingDetail && (
          <p className="font-typewriter text-sm text-saul-black/60">Loading transcript…</p>
        )}
        {selectedId && detail?.data && (
          <div>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="font-display text-xl tracking-wide text-saul-black">Transcript</h3>
              <StateBadge state={detail.data.state} />
            </div>
            <TranscriptView transcript={detail.data.transcript} />
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatSessionViewer;
