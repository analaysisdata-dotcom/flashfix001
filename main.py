import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# --- 📢 TELEGRAM CONFIG ---
# Yahan apna Token aur ID dalein (BotFather aur userinfobot se lekar)
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE" 
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

def send_to_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

DB_FILE = "raza_electrical_db.json"

class Worker(BaseModel):
    name: str
    phone: str
    upi: str
    skill: str

class Booking(BaseModel):
    id: int = 0
    service: str
    phone: str
    address: str
    lat: float = 0.0
    lon: float = 0.0
    status: str = "Pending"
    assigned_to: str = ""

class Review(BaseModel):
    id: int = 0
    name: str
    comment: str

def get_db():
    if not os.path.exists(DB_FILE): 
        return {"workers": [], "bookings": [], "reviews": [], "pending_workers": []}
    try:
        with open(DB_FILE, "r") as f: 
            data = json.load(f)
            if "pending_workers" not in data: data["pending_workers"] = []
            return data
    except: 
        return {"workers": [], "bookings": [], "reviews": [], "pending_workers": []}

def save_db(data):
    with open(DB_FILE, "w") as f: 
        json.dump(data, f, indent=4)

@app.get("/get-data")
def get_data():
    return get_db()

# --- WORKER REQUEST & NOTIFICATION ---
@app.post("/add-worker-request")
def add_worker_request(w: Worker):
    db = get_db()
    db["pending_workers"].append(w.dict())
    save_db(db)
    
    msg = f"👷 NAYA WORKER REQUEST!\n\n👤 Name: {w.name}\n📞 Phone: {w.phone}\n🛠 Skill: {w.skill}\n💰 UPI: {w.upi}\n\nSir, Admin panel khol kar Approve karein."
    send_to_telegram(msg)
    return {"status": "Success"}

@app.post("/approve-worker/{phone}")
def approve_worker(phone: str):
    db = get_db()
    worker = next((w for w in db["pending_workers"] if w["phone"] == phone), None)
    if worker:
        db["workers"].append(worker)
        db["pending_workers"] = [w for w in db["pending_workers"] if w["phone"] != phone]
        save_db(db)
        return {"status": "Success"}
    return {"status": "Error"}

# --- BOOKING & NOTIFICATION ---
@app.post("/book")
def book(b: Booking):
    db = get_db()
    b.id = len(db["bookings"]) + 1
    db["bookings"].append(b.dict())
    save_db(db)
    
    msg = f"💰 NAYI BOOKING!\n\n🛠 Service: {b.service}\n📍 Address: {b.address}\n📞 Customer: {b.phone}"
    send_to_telegram(msg)
    return {"status": "Success"}

@app.post("/add-review")
def add_review(r: Review):
    db = get_db()
    r.id = len(db.get("reviews", [])) + 1
    db["reviews"].append(r.dict())
    save_db(db)
    return {"status": "Success"}

@app.delete("/delete-review/{review_id}")
def delete_review(review_id: int):
    db = get_db()
    db["reviews"] = [r for r in db["reviews"] if r.get("id") != review_id]
    save_db(db)
    return {"status": "Success"}