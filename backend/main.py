from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.session import create_all_tables
from routes.chat import router as chat_router

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
