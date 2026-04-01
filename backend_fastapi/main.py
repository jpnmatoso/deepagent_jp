from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes import assistants, threads, runs


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Backend FastAPI starting up...")
    yield
    print("Backend FastAPI shutting down...")


app = FastAPI(
    title="Deep Agents API (FastAPI)",
    description="Custom backend for Deep Agents - compatible with LangGraph SDK",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assistants.router)
app.include_router(threads.router)
app.include_router(runs.router)


@app.get("/health")
async def health():
    return {"status": "ok", "backend": "fastapi"}


@app.get("/")
async def root():
    return {"message": "Deep Agents FastAPI Backend", "version": "1.0.0"}
