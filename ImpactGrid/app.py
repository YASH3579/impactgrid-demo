import os, sqlite3, hashlib, secrets, json, re
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(ROOT / "data" / "impactgrid.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="ImpactGrid API", version="1.0.0")
#app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
          salt TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'member',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS records(
          id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
          data TEXT NOT NULL, owner_id INTEGER, created_at TEXT NOT NULL,
          FOREIGN KEY(owner_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS sessions(
          token TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
          created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)
init_db()

def now(): return datetime.utcnow().isoformat(timespec="seconds") + "Z"
def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 180000).hex()

class Signup(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str
    password: str = Field(min_length=8, max_length=128)
class Login(BaseModel):
    email: str
    password: str
class RecordIn(BaseModel):
    kind: str = Field(min_length=2, max_length=50)
    data: dict

def get_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    with db() as c:
        row = c.execute("SELECT users.id,users.name,users.email,users.role FROM sessions JOIN users ON users.id=sessions.user_id WHERE token=?", (token,)).fetchone()
    return dict(row) if row else None

@app.get("/")
def home(): return FileResponse(ROOT / "static" / "index.html")

@app.get("/api/health")
def health(): return {"ok": True, "service": "ImpactGrid API", "time": now()}

@app.post("/api/signup")
def signup(body: Signup):
    email = body.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(400, "Please enter a valid email.")
    salt = secrets.token_hex(16)
    with db() as c:
        try:
            cur = c.execute("INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)",
                (body.name.strip(), email, hash_password(body.password, salt), salt, "member", now()))
            uid = cur.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(409, "An account with this email already exists.")
        token = secrets.token_urlsafe(32)
        c.execute("INSERT INTO sessions(token,user_id,created_at) VALUES(?,?,?)", (token, uid, now()))
    return {"token": token, "user": {"id": uid, "name": body.name.strip(), "email": email, "role":"member"}}

@app.post("/api/login")
def login(body: Login):
    with db() as c:
        u = c.execute("SELECT * FROM users WHERE email=?", (body.email.strip().lower(),)).fetchone()
        if not u or hash_password(body.password, u["salt"]) != u["password_hash"]:
            raise HTTPException(401, "Incorrect email or password.")
        token = secrets.token_urlsafe(32)
        c.execute("INSERT INTO sessions(token,user_id,created_at) VALUES(?,?,?)", (token, u["id"], now()))
    return {"token": token, "user":{"id":u["id"],"name":u["name"],"email":u["email"],"role":u["role"]}}

@app.post("/api/logout")
def logout(authorization: Optional[str] = Header(default=None)):
    if authorization and authorization.lower().startswith("bearer "):
        with db() as c: c.execute("DELETE FROM sessions WHERE token=?", (authorization.split(" ",1)[1].strip(),))
    return {"ok":True}

@app.get("/api/me")
def me(user=Depends(get_user)):
    if not user: raise HTTPException(401, "Sign in to view your profile.")
    return user

@app.get("/api/records")
def list_records(kind: Optional[str]=None, user=Depends(get_user)):
    with db() as c:
        if kind:
            rows = c.execute("SELECT * FROM records WHERE kind=? ORDER BY id DESC LIMIT 100", (kind,)).fetchall()
        else:
            rows = c.execute("SELECT * FROM records ORDER BY id DESC LIMIT 100").fetchall()
    return [{"id":r["id"],"kind":r["kind"],"data":json.loads(r["data"]),"owner_id":r["owner_id"],"created_at":r["created_at"]} for r in rows]

@app.post("/api/records")
def create_record(body: RecordIn, user=Depends(get_user)):
    if not user: raise HTTPException(401, "Sign in first to save your work.")
    with db() as c:
        cur = c.execute("INSERT INTO records(kind,data,owner_id,created_at) VALUES(?,?,?,?)",
                        (body.kind, json.dumps(body.data, ensure_ascii=False), user["id"], now()))
    return {"id":cur.lastrowid,"kind":body.kind,"data":body.data,"created_at":now()}

@app.delete("/api/records/{record_id}")
def delete_record(record_id: int, user=Depends(get_user)):
    if not user: raise HTTPException(401, "Sign in first.")
    with db() as c:
        row = c.execute("SELECT owner_id FROM records WHERE id=?", (record_id,)).fetchone()
        if not row: raise HTTPException(404, "Record not found.")
        if row["owner_id"] != user["id"] and user["role"] != "admin": raise HTTPException(403, "You can delete only your own records.")
        c.execute("DELETE FROM records WHERE id=?", (record_id,))
    return {"ok":True}

class StudyAsk(BaseModel):
    question: str = Field(min_length=2, max_length=3000)
    language: str = "Hindi / Hinglish"
    notes: str = Field(default="", max_length=5000)
@app.post("/api/ai/study")
def study(body: StudyAsk):
    # Optional provider integration: configure OPENAI_API_KEY and install openai.
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = f"Explain clearly in {body.language}. Use simple language, steps and an example. If unsure, say so. Notes/context: {body.notes}\nQuestion: {body.question}"
            result = client.chat.completions.create(model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
                messages=[{"role":"system","content":"You are a safe, patient study tutor. Do not invent textbook citations."},{"role":"user","content":prompt}],
                temperature=0.3)
            return {"answer":result.choices[0].message.content,"mode":"AI API"}
        except Exception as e:
            return {"answer":fallback_study(body.question, body.language, body.notes) + "\n\n(Note: AI provider unavailable; showing local fallback.)","mode":"local fallback"}
    return {"answer":fallback_study(body.question, body.language, body.notes),"mode":"local fallback"}

def fallback_study(q, language, notes):
    ql=q.lower()
    if any(x in ql for x in ["photosynthesis","प्रकाश संश्लेषण"]):
        return "Photosynthesis (प्रकाश संश्लेषण) वह प्रक्रिया है जिसमें पौधे sunlight, water और carbon dioxide की मदद से अपना भोजन (glucose) बनाते हैं और oxygen छोड़ते हैं.\n\nSteps:\n1. पत्तियाँ sunlight absorb करती हैं.\n2. जड़ें पानी लेती हैं.\n3. पत्तियाँ हवा से CO₂ लेती हैं.\n4. पौधा glucose बनाता है और oxygen release करता है.\n\nExample: धूप में रखा हरा पौधा photosynthesis करता है."
    if any(x in ql for x in ["fraction","भिन्न"]):
        return "Fraction (भिन्न) किसी whole के हिस्से को दिखाता है. जैसे 3/4 में 3 numerator (ऊपर) और 4 denominator (नीचे) है. Pizza के 4 बराबर टुकड़ों में से 3 टुकड़े = 3/4."
    return f"Study Buddy ({language})\n\nYour question: {q}\n\nTry this structure:\n1. Topic को छोटे हिस्सों में बाँटें.\n2. पहले definition समझें.\n3. एक real-life example लिखें.\n4. अपने शब्दों में 2-line summary बनाएँ.\n5. बिना notes देखे एक practice question हल करें.\n\n{('Your notes/context: ' + notes[:800]) if notes else 'Tip: Add your textbook notes in the Notes field for a more focused explanation.'}\n\nFor stronger AI answers, configure OPENAI_API_KEY in your .env file."

class CropCheck(BaseModel):
    crop: str
    symptoms: str = Field(min_length=3, max_length=2000)
@app.post("/api/ai/crop-check")
def crop_check(body: CropCheck):
    s=body.symptoms.lower()
    if any(k in s for k in ["yellow","पीला","yellowing","chlorosis"]):
        likely="Possible nutrient deficiency or watering/root stress"
        actions=["Check whether yellowing starts on older or newer leaves.","Inspect soil moisture and drainage before adding fertilizer.","Compare with local agriculture-extension guidance and test soil if possible."]
    elif any(k in s for k in ["spot","दाग","lesion","fungus","fungal"]):
        likely="Possible leaf-spot disease; cause cannot be confirmed from text alone"
        actions=["Avoid wetting leaves during irrigation.","Remove badly affected fallen leaves if safe to do so.","Ask a local agriculture officer to confirm before applying any pesticide."]
    elif any(k in s for k in ["curl","मुड़","wilt","मुरझ"]):
        likely="Possible pest, heat, water stress, or disease"
        actions=["Check underside of leaves for pests.","Check soil moisture and recent heat exposure.","Get local expert confirmation before treatment."]
    else:
        likely="Insufficient information for a reliable diagnosis"
        actions=["Upload clear photos in a future image-enabled version (whole plant, upper and lower leaf).","Note crop variety, plant age, weather and spread pattern.","Consult a local agriculture expert before using pesticides."]
    return {"crop":body.crop,"possible_cause":likely,"actions":actions,"disclaimer":"This is a preliminary educational triage, not a confirmed diagnosis. Do not apply pesticides or fertilizers solely from this result."}

@app.get("/api/modules")
def modules():
    return MODULES

MODULES = [
{"id":"PS-01","category":"AgriTech & Rural Innovation","title":"CROP-SCAN: Crop Disease & Deficiency Detection","difficulty":"Hard","description":"Early crop symptom triage with safe next steps and expert referral."},
{"id":"PS-02","category":"Healthcare & Wellness","title":"Blood Donor Finder","difficulty":"Medium","description":"Register donor availability and search by blood group and area. Contact details are demo data until verified."},
{"id":"PS-03","category":"AI & Generative AI","title":"Multilingual Study Buddy","difficulty":"Hard","description":"Ask study questions in Hindi/Hinglish; optional AI API and local fallback."},
{"id":"PS-04","category":"Cybersecurity & Digital Safety","title":"Cyber Safety Game for Kids & Elders","difficulty":"Medium","description":"Learn to spot OTP scams, suspicious links and impersonation."},
{"id":"PS-05","category":"Open Innovation","title":"Local Artisan & Small Business Marketplace","difficulty":"Medium","description":"Showcase products and save demo listings to the database."},
{"id":"PS-06","category":"Smart City & Civic Tech","title":"Cooperative-Based Household Services Booking","difficulty":"Hard","description":"Create a service request for electricians, plumbers, cooks and more."},
{"id":"PS-07","category":"Open Innovation","title":"Community Problem-Solving Platform","difficulty":"Medium","description":"Post local issues and invite teams to help."},
{"id":"PS-08","category":"Smart Education & Campus","title":"IT Streams vs. Non-IT Streams","difficulty":"Medium","description":"Explore transferable skills and pathways into digital careers."},
{"id":"PS-09","category":"Smart Education & Campus","title":"Gen Z Needs New Learning Styles","difficulty":"Medium","description":"Build a study plan and track progress."},
{"id":"PS-10","category":"Smart Education & Campus","title":"Faculty-Student Disconnect","difficulty":"Medium","description":"Submit constructive feedback to improve communication."},
{"id":"PS-11","category":"Smart Education & Campus","title":"Fragmented ERP Systems, Lack of AI Integration & Workflow Automation","difficulty":"Hard","description":"Unified dashboard for common campus workflows and tasks."}
]
