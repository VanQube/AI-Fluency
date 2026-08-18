import { useAuth0 } from '@auth0/auth0-react';

// Epic E3 — the real gate is the backend's require_admin dependency
// (backend/admin_auth.py); this only keeps a logged-out browser from
// rendering the admin UI at all.
function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading, loginWithRedirect } = useAuth0();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-saul-cream font-typewriter text-saul-black">
        Loading…
      </div>
    );
  }

  if (!isAuthenticated) {
    loginWithRedirect();
    return null;
  }

  return children;
}

export default ProtectedRoute;
