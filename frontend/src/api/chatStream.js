// POST /chat/stream is deliberately excluded from the OpenAPI schema
// (backend/routes/chat.py) — same carve-out Section 4.8 describes for the
// WebSocket path: an SSE/WS body has no normal JSON response shape for
// FastAPI to describe, so there's no generated React Query hook for it.
// The `ChatStreamEvent` type itself still comes from the generated file,
// exported via the dummy endpoint in backend/routes/_types_chat_events.py —
// only the fetch call here is hand-written.
const BASE_URL = 'http://localhost:8000';

export async function* streamChatMessage({ session_id, message }, { signal } = {}) {
  const response = await fetch(`${BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id, message }),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Stream request failed: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary;
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const dataLine = rawEvent.split('\n').find((line) => line.startsWith('data: '));
      if (!dataLine) continue;
      yield JSON.parse(dataLine.slice('data: '.length));
    }
  }
}
