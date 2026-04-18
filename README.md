# Profile Intelligence Service

A simple backend API built with FastAPI that takes a name, enriches it using external APIs (Genderize, Agify, Nationalize), stores the result in a database, and provides endpoints to manage the data.

---

## 🚀 Features

* Create a profile from a name
* Fetch a single profile
* Fetch all profiles with optional filters
* Delete a profile
* Prevent duplicate entries (idempotency)
* Case-insensitive filtering

---

## 🛠 Tech Stack

* FastAPI
* SQLite
* SQLAlchemy
* httpx
* UUID v7

---

## ⚙️ Setup

Clone the repository:

```bash
git clone https://github.com/abolade20/profile_intellect.git
cd profile_intellect
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
uvicorn app.main:app --reload
```

---

## 📡 API Endpoints

### 1. Create Profile

POST /api/profiles

Request body:

```json
{
  "name": "ella"
}
```

---

### 2. Get Profile by ID

GET /api/profiles/{id}

---

### 3. Get All Profiles (with optional filters)

GET /api/profiles?gender=male&country_id=NG&age_group=adult

---

### 4. Delete Profile

DELETE /api/profiles/{id}

---

## ❗ Error Format

All errors follow this structure:

```json
{
  "status": "error",
  "message": "error message"
}
```

---

## 🌍 External APIs Used

* https://api.genderize.io
* https://api.agify.io
* https://api.nationalize.io

---

## 🔗 Live API

(Add your deployed URL here after deployment)

---

## 📝 Notes

* Names are stored in lowercase to prevent duplicates
* Filtering is case-insensitive
* UUID v7 is used for IDs
* Timestamps are in UTC (ISO 8601)

---

## 📌 Task

This project was built for the HNG Backend Stage 1 task (Data Persistence & API Design).
