from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import logger
from api.routes import router as api_router
from models.database import init_db

# Initialize the FastAPI app
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Initialize the database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing application...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

@app.get("/")
async def root():
    return {"message": "Welcome to the NLP Keyword Extractor API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)