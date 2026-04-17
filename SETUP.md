# Profile Intelligence Service - Setup & Deployment Guide

## Overview
This is a complete backend implementation of the Profile Intelligence Service according to the PRD. All code is in a single `main.py` file using FastAPI.

## Prerequisites
- Python 3.8+
- pip (Python package manager)

## Local Development Setup

### 1. Create a virtual environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application locally
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 4. API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database
- **Default**: SQLite (`profiles.db`)
- **Production**: PostgreSQL (set `DATABASE_URL` in `.env`)

## Environment Variables
Create a `.env` file (copy from `.env.example`):
```
DATABASE_URL=sqlite:///./profiles.db
PORT=8000
```

## API Endpoints

### Health Check
```
GET /health
```

### Create Profile
```
POST /api/profiles
Content-Type: application/json

{
  "name": "ella"
}
```

**Response (201 Created or 200 if already exists):**
```json
{
  "status": "success",
  "data": {
    "id": "UUID",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 5000,
    "age": 28,
    "age_group": "adult",
    "country_id": "US",
    "country_probability": 0.15,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

### Get Single Profile
```
GET /api/profiles/{id}
```

### Get All Profiles (with optional filtering)
```
GET /api/profiles?gender=female&country_id=US&age_group=adult
```

Query Parameters:
- `gender` (optional): Filter by gender (case-insensitive)
- `country_id` (optional): Filter by country ID (case-insensitive)
- `age_group` (optional): Filter by age group (case-insensitive)

### Delete Profile
```
DELETE /api/profiles/{id}
```

Returns `204 No Content` on success.

## Deployment Options

### Railway.app (Recommended)
1. Push code to GitHub
2. Go to [Railway.app](https://railway.app)
3. Connect your GitHub repository
4. Set environment variables in Railway dashboard
5. Deploy

### Heroku
1. Install Heroku CLI
2. Create a `Procfile`:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
3. Deploy:
   ```bash
   heroku create your-app-name
   heroku config:set DATABASE_URL=postgresql://...
   git push heroku main
   ```

### AWS (EC2 + RDS)
1. Launch EC2 instance with Python installed
2. Clone repository and install dependencies
3. Use RDS for PostgreSQL database
4. Set `DATABASE_URL` environment variable
5. Run with `uvicorn` or use Gunicorn for production

### Vercel (Serverless)
Note: Serverless deployment has limitations. Use a traditional server (Railway, Heroku, AWS) for better performance.

## Error Handling
All errors follow the standard format:
```json
{
  "status": "error",
  "message": "error message"
}
```

Status Codes:
- `400`: Missing or empty name
- `404`: Profile not found
- `422`: Invalid data type
- `502`: External API failure
- `500`: Internal server error

## Testing

### Example: Create a profile
```bash
curl -X POST http://localhost:8000/api/profiles \
  -H "Content-Type: application/json" \
  -d '{"name": "ella"}'
```

### Example: Get all profiles
```bash
curl http://localhost:8000/api/profiles
```

### Example: Filter by gender
```bash
curl http://localhost:8000/api/profiles?gender=female
```

## Features Implemented
✅ Integration with Genderize, Agify, and Nationalize APIs
✅ Data enrichment and processing
✅ SQLite/PostgreSQL database persistence
✅ UUID v7 generation for profile IDs
✅ ISO 8601 UTC timestamps
✅ CORS enabled (cross-origin requests allowed)
✅ Idempotency (no duplicate names)
✅ Case-insensitive filtering
✅ Proper error handling and validation
✅ RESTful API design

## Performance Notes
- API response time depends on external API latency (typically 1-3 seconds)
- Database queries are indexed on `name` and `id` for fast lookups
- CORS middleware enabled for frontend integration

## Next Steps for Production
1. Use PostgreSQL instead of SQLite
2. Add rate limiting middleware
3. Implement request logging
4. Use Gunicorn/Uvicorn workers for concurrency
5. Add database migrations (Alembic)
6. Implement monitoring and alerting
