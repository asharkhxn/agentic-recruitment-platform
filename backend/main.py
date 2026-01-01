from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_router, jobs_router, applications_router, agent_router, files_router, ats_router
import os
from core.config import Config

# Initialize LangSmith observability
# LangSmith automatically traces LangChain and LangGraph components when env vars are set
if Config.LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = Config.LANGSMITH_TRACING_V2
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = Config.LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = Config.LANGSMITH_PROJECT
    print(f"✅ LangSmith observability enabled for project: {Config.LANGSMITH_PROJECT}")
else:
    print("⚠️  LangSmith API key not found. Observability disabled.")

app = FastAPI(title="Recruitment System API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
async def root():
    return {"status": "healthy", "message": "Recruitment System API"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Register routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(applications_router, prefix="/applications", tags=["applications"])
app.include_router(agent_router, prefix="/agent", tags=["agent"])
app.include_router(files_router, prefix="/files", tags=["files"])
app.include_router(ats_router, prefix="/ats", tags=["ats"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
