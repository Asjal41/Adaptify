import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import engine
import models
from routers import auth_routes as auth_router, teacher, student, assignment

# Create all DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Adaptify",
    description="AI-powered personalized assignment generation system using Cognitive Learning Theory",
    version="1.0.0"
)

# CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler — logs full traceback
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"\n{'='*60}\nUNHANDLED EXCEPTION on {request.method} {request.url}\n{tb}\n{'='*60}\n")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {type(exc).__name__}: {str(exc)}"}
    )


# Include all routers
app.include_router(auth_router.router)
app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(assignment.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Adaptify Backend is running ✅",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
