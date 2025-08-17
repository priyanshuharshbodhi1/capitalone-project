from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes_chat import router as chat_router
from .routes_plantdoc import router as plantdoc_router
from ..infra.settings import settings

app = FastAPI(title="Project Kisan Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allow_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/agent", tags=["agent"])
app.include_router(plantdoc_router, prefix="/api", tags=["plantdoc"])


@app.get("/health")
def health():
    return {"status": "ok"}
