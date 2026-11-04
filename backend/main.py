import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from database.db import init_db
from services.executor import engine_name
from services import llm


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="SOCH API", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:4173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(router, prefix="/api")


@app.get("/api/health")
def health():
    return {"ok": True, "product": "SOCH", "executor": engine_name(), "llm": llm.status()}
