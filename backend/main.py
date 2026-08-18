import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.session import create_all_tables
from routes._types_chat_events import router as types_chat_events_router
from routes.admin import router as admin_router
from routes.chat import router as chat_router
from routes.verify import router as verify_router

# INFO so the mock-SMS code log (tools/send_verification_code.py) is
# actually visible in `docker compose logs backend` during a demo.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

app = FastAPI(title="SecureShip Backend", version="0.1.0")

# Frontend (localhost:3000) and backend (localhost:8000) are different
# origins. Locked to the known dev origin rather than "*" as a baseline
# security habit (Section 4.3's "no PII in logs" spirit).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_all_tables()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(chat_router)
app.include_router(verify_router)
app.include_router(admin_router)
app.include_router(types_chat_events_router)
