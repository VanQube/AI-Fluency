// Every generated admin hook (frontend/src/api/generated/secureship.ts)
// takes an optional `fetch: RequestInit` override — this attaches the
// Auth0 access token as a Bearer header so backend/admin_auth.py's
// require_admin dependency accepts the request.
export function authFetch(token) {
  return token ? { headers: { Authorization: `Bearer ${token}` } } : undefined;
}
