from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time
import logging

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors.
    """
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add process time header to response.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to the E-Commerce Product Catalog API"}

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Startup event to initialize the database with sample data if needed
@app.on_event("startup")
async def initialize_db():
    """
    Initialize the database with sample data on startup
    """
    if settings.ENVIRONMENT == "dev":
        try:
            from app.db.init_db import init_db
            logging.info("Initializing database with sample data")
            await init_db()
        except Exception as e:
            logging.error(f"Error initializing database: {e}")

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
