from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(
    title="Deep Agents API",
    description="Custom routes for Deep Agents Backend",
    version="1.0.0",
)


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Agent-Backend"] = "langgraph"
        return response


app.add_middleware(CustomHeaderMiddleware)


@app.get("/health")
async def health():
    return {"status": "ok", "backend": "langgraph"}


@app.get("/agents")
async def list_agents():
    return {
        "agents": [
            {
                "id": "planning",
                "name": "Planning Agent",
                "description": "Strategic planning agent",
            },
            {
                "id": "research",
                "name": "Research Agent",
                "description": "Deep research agent",
            },
        ]
    }
