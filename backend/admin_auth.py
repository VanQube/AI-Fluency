import os

from fastapi_plugin import Auth0FastAPI

# Epic E3 — every /admin/* route depends on require_admin. Domain/audience
# come from env vars (docker-compose.yml's backend `environment:` block),
# matching the OLLAMA_HOST/DATABASE_URL convention already used elsewhere —
# no .env file in this project.
AUTH0_DOMAIN = os.environ["AUTH0_DOMAIN"]
AUTH0_AUDIENCE = os.environ["AUTH0_AUDIENCE"]

_auth0 = Auth0FastAPI(domain=AUTH0_DOMAIN, audience=AUTH0_AUDIENCE)

# FastAPI dependency: validates the bearer token's signature/issuer/audience
# against the tenant's JWKS. Any authenticated Auth0 user is treated as an
# admin — no separate allowlist/role check (confirmed policy, 2026-08-15).
require_admin = _auth0.require_auth()
