"""
Profile Intelligence Service - Complete Single File Implementation

A backend system that enriches user profiles by calling external APIs,
processing data, storing it in a database, and exposing RESTful endpoints.

All functionality consolidated into single main.py for simplicity.
"""

# ============================================================================
# IMPORTS
# ============================================================================

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from uuid6 import uuid7
from datetime import datetime
from pydantic import BaseModel
import httpx


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASE_URL = "sqlite:///./profiles.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CreateProfileRequest(BaseModel):
    """Request model for creating a profile."""
    name: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "ella"
            }
        }


# ============================================================================
# ORM MODEL - Profile
# ============================================================================

class Profile(Base):
    """Profile entity model with all enriched user data."""
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    gender = Column(String)
    gender_probability = Column(Float)
    sample_size = Column(Integer)
    age = Column(Integer)
    age_group = Column(String)
    country_id = Column(String)
    country_probability = Column(Float)
    created_at = Column(String)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def classify_age(age: int) -> str:
    """Classify age into age groups per PRD requirements."""
    if age <= 12:
        return "child"
    elif age <= 19:
        return "teenager"
    elif age <= 59:
        return "adult"
    else:
        return "senior"


async def fetch_external(name: str) -> dict:
    """
    Fetch and process data from external APIs.

    Calls Genderize, Agify, and Nationalize APIs.
    Returns processed profile data or raises 502 error if invalid.
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        g = await client.get(f"https://api.genderize.io?name={name}")
        a = await client.get(f"https://api.agify.io?name={name}")
        n = await client.get(f"https://api.nationalize.io?name={name}")

    g, a, n = g.json(), a.json(), n.json()

    # Validate Genderize response
    if g.get("gender") is None or g.get("count") is None or g.get("count") == 0:
        raise HTTPException(502, "Genderize returned an invalid response")

    # Validate Agify response
    if a.get("age") is None:
        raise HTTPException(502, "Agify returned an invalid response")

    # Validate Nationalize response
    if not n.get("country"):
        raise HTTPException(502, "Nationalize returned an invalid response")

    # Select country with highest probability
    best_country = max(n["country"], key=lambda x: x["probability"])

    return {
        "gender": g["gender"],
        "gender_probability": g["probability"],
        "sample_size": g["count"],
        "age": a["age"],
        "age_group": classify_age(a["age"]),
        "country_id": best_country["country_id"],
        "country_probability": best_country["probability"],
    }


# ============================================================================
# CRUD FUNCTIONS
# ============================================================================

def get_by_name(db, name: str):
    """Get profile by name (for idempotency check)."""
    return db.query(Profile).filter(Profile.name == name).first()


def get_by_id(db, id: str):
    """Get profile by ID."""
    return db.query(Profile).filter(Profile.id == id).first()


def get_all(db, gender: str = None, country_id: str = None, age_group: str = None):
    """Get all profiles with optional case-insensitive filtering."""
    query = db.query(Profile)

    if gender:
        query = query.filter(Profile.gender.ilike(gender))
    if country_id:
        query = query.filter(Profile.country_id.ilike(country_id))
    if age_group:
        query = query.filter(Profile.age_group.ilike(age_group))

    return query.all()


def create_profile(db, profile: Profile) -> Profile:
    """Create and save a new profile."""
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def delete_profile(db, profile: Profile) -> None:
    """Delete a profile from database."""
    db.delete(profile)
    db.commit()


# ============================================================================
# RESPONSE SCHEMA FUNCTIONS
# ============================================================================

def profile_full(p):
    """Full profile response (all 10 fields)."""
    return {
        "id": p.id,
        "name": p.name,
        "gender": p.gender,
        "gender_probability": p.gender_probability,
        "sample_size": p.sample_size,
        "age": p.age,
        "age_group": p.age_group,
        "country_id": p.country_id,
        "country_probability": p.country_probability,
        "created_at": p.created_at,
    }


def profile_list(p):
    """Partial profile response (for GET all)."""
    return {
        "id": p.id,
        "name": p.name,
        "gender": p.gender,
        "age": p.age,
        "age_group": p.age_group,
        "country_id": p.country_id,
    }


# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Profile Intelligence Service",
    description="Backend API for profile enrichment and management"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/api/profiles")
async def create_profile_endpoint(req: CreateProfileRequest):
    """Create a new profile or return existing one if name already exists."""
    name = req.name

    # Validate type is string (Pydantic already validates this)
    if not isinstance(name, str):
        raise HTTPException(422, "Invalid type")

    # Normalize: strip whitespace
    name = name.strip()

    # Validate not empty after strip
    if not name:
        raise HTTPException(400, "Missing or empty name")

    db = SessionLocal()

    try:
        # Check idempotency (case-insensitive)
        existing = db.query(Profile).filter(Profile.name.ilike(name)).first()
        if existing:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Profile already exists",
                    "data": profile_full(existing),
                }
            )

        # Fetch from external APIs
        data = await fetch_external(name)

        # Create profile
        profile = Profile(
            id=str(uuid7()),
            name=name,
            created_at=datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            **data,
        )

        # Save to database
        profile = create_profile(db, profile)

        # Return 201 Created
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "data": profile_full(profile),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(500, "Internal server error")
    finally:
        db.close()


@app.get("/api/profiles/{id}")
def get_profile(id: str):
    """Retrieve a single profile by ID."""
    db = SessionLocal()

    try:
        profile = get_by_id(db, id)

        if not profile:
            raise HTTPException(404, "Profile not found")

        return {
            "status": "success",
            "data": profile_full(profile),
        }

    finally:
        db.close()


@app.get("/api/profiles")
def get_profiles(gender: str = None, country_id: str = None, age_group: str = None):
    """Retrieve all profiles with optional case-insensitive filtering."""
    db = SessionLocal()
    try:
        profiles = get_all(db, gender, country_id, age_group)

        return {
            "status": "success",
            "count": len(profiles),
            "data": [profile_list(p) for p in profiles],
        }
    finally:
        db.close()


@app.delete("/api/profiles/{id}")
def delete_profile_by_id(id: str):
    """Delete a profile by ID."""
    db = SessionLocal()
    try:
        profile = get_by_id(db, id)

        if not profile:
            raise HTTPException(404, "Profile not found")

        delete_profile(db, profile)
        return Response(status_code=204)
    finally:
        db.close()


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# GLOBAL ERROR HANDLER
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle all HTTP exceptions with standard error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )
