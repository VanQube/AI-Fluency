import { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import CustomerManager from './CustomerManager';
import ShipmentManager from './ShipmentManager';
import PackageManager from './PackageManager';
import ChatSessionViewer from './ChatSessionViewer';

const TABS = {
  customers: { label: 'Customers', Component: CustomerManager },
  shipments: { label: 'Shipments', Component: ShipmentManager },
  packages: { label: 'Packages', Component: PackageManager },
  sessions: { label: 'Chat Sessions', Component: ChatSessionViewer },
};

// Epic E. ProtectedRoute (App.js) already guarantees isAuthenticated here —
// this component's job is just getting an access token onto every admin
// API call (authFetch.js) so backend/admin_auth.py's require_admin dependency
// accepts the requests. Real gating lives on the backend (Epic E3); this is
// UX, not the security boundary.
function AdminApp() {
  const { user, logout, getAccessTokenSilently } = useAuth0();
  const [tab, setTab] = useState('customers');
  const [token, setToken] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getAccessTokenSilently()
      .then((t) => {
        if (!cancelled) setToken(t);
      })
      .catch(() => {
        // Silent-auth failure (e.g. token expired mid-session) — the next
        // API call will 401, which is an acceptable fallback here since a
        // full re-login is one click via ProtectedRoute's loginWithRedirect.
      });
    return () => {
      cancelled = true;
    };
  }, [getAccessTokenSilently]);

  const ActiveManager = TABS[tab].Component;

  return (
    <div className="min-h-screen bg-saul-cream p-6">
      <div className="mx-auto max-w-5xl">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="font-display text-4xl tracking-wide text-saul-black">
            SecureShip Admin
          </h1>
          <div className="flex items-center gap-3 font-typewriter text-sm text-saul-black">
            <span>{user?.email}</span>
            <button
              type="button"
              onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
              className="rounded-sm border border-saul-black/30 px-3 py-1 text-xs"
            >
              Log out
            </button>
          </div>
        </div>

        <div className="mb-6 flex gap-2 border-b-2 border-saul-black/20">
          {Object.entries(TABS).map(([key, { label }]) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={`px-4 py-2 font-display text-lg tracking-wide ${
                tab === key
                  ? 'border-b-2 border-saul-teal text-saul-teal'
                  : 'text-saul-black/60'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {token ? (
          <ActiveManager token={token} />
        ) : (
          <p className="font-typewriter text-sm text-saul-black/60">Authenticating…</p>
        )}
      </div>
    </div>
  );
}

export default AdminApp;
