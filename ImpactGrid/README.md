# ImpactGrid — Full-stack hackathon starter

One responsive web app covering the 11 ImpactGrid/Hackways problem statements.

## Stack
- Frontend: HTML, CSS, JavaScript
- Backend: Python + FastAPI
- Database: SQLite (zero separate database server required; suitable for demo)
- AI: Optional OpenAI-compatible API integration for Study Buddy; local fallback works without an API key
- Crop checker: cautious rule-based symptom triage, not a medical/agronomic diagnosis

## Run on Windows
1. Install Python 3.10+ from python.org and enable "Add Python to PATH".
2. Extract this ZIP.
3. Open Command Prompt/PowerShell in the extracted `impactgrid_fullstack` folder.
4. Run:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   uvicorn app:app --reload
   ```
5. Open http://127.0.0.1:8000
6. API docs: http://127.0.0.1:8000/docs

## Optional AI
Install `openai` (`pip install "openai>=1.30,<2.0"`), add your own API key to `.env`, and load it into your shell before starting the server. Easiest on Windows PowerShell:
```powershell
$env:OPENAI_API_KEY="YOUR_KEY_HERE"
$env:OPENAI_MODEL="gpt-4o-mini"
uvicorn app:app --reload
```
Never put an API key in frontend JavaScript or commit it to GitHub. API usage may cost money. Without a key, Study Buddy returns a local guided fallback.

## Included functionality
- Responsive single-page UI and searchable/filterable 11-module directory
- Sign up, login, logout; passwords are PBKDF2-hashed
- SQLite-backed records for authenticated users
- Study Buddy endpoint with optional AI provider
- Crop symptom triage with safety guidance
- Interactive cyber-safety quiz
- Donor finder, artisan listings, service bookings, community issues, career explorer, study planner, faculty feedback and campus workflow demos
- API health endpoint and interactive Swagger docs

## Honest demo limitations
- Donor entries and marketplace/services records are demo data, not verified real-world services.
- No SMS/email OTP, identity verification, live geolocation, payment processing, or production deployment is configured.
- Crop symptom triage is not a confirmed diagnosis; use a local agriculture expert before treatment.
- For public deployment, add HTTPS, rate limiting, CSRF/CORS policy, password reset, audit logging, backups, moderation, privacy notice and appropriate professional review.


## Hosting
See `DEPLOYMENT.md` and `render.yaml` for a Render Blueprint deployment. Hosting may require a paid persistent disk for SQLite persistence. For production, use managed PostgreSQL and complete a security review.
