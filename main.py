from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- EK HI PERMANENT DATABASE ---
DB_FILE = "raza_electrical_db.json"

class Worker(BaseModel):
    name: str; phone: str; upi: str; skill: str

class Booking(BaseModel):
    id: int = 0; service: str; phone: str; address: str; lat: float = 0.0; lon: float = 0.0
    status: str = "Pending"; assigned_to: str = ""; final_amount: float = 0.0
    payment_mode: str = ""; commission_due: float = 0.0

def get_db():
    if not os.path.exists(DB_FILE): return {"workers": [], "bookings": [], "reviews": []}
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {"workers": [], "bookings": [], "reviews": []}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

@app.get("/get-data")
def get_data(): return get_db()

@app.post("/add-worker")
def add_worker(w: Worker):
    db = get_db(); db["workers"].append(w.dict()); save_db(db)
    return {"status": "Success"}

@app.post("/book")
def book(b: Booking):
    db = get_db(); b.id = len(db["bookings"]) + 1
    db["bookings"].append(b.dict()); save_db(db)
    return {"status": "Success"}

@app.post("/update-job/{job_id}/{worker_phone}/{status}")
def update_job(job_id: int, worker_phone: str, status: str):
    db = get_db()
    for j in db["bookings"]:
        if j["id"] == job_id:
            j["status"] = status; j["assigned_to"] = worker_phone
            save_db(db); return {"status": "Success"}
    return {"status": "Error"}

@app.post("/complete-job/{job_id}/{amount}/{mode}")
def complete_job(job_id: int, amount: float, mode: str):
    db = get_db()
    for j in db["bookings"]:
        if j["id"] == job_id:
            j["status"] = "Completed"
            j["final_amount"] = amount
            j["payment_mode"] = mode
            # Sirf Cash par aapka 10% commission calculate hoga
            j["commission_due"] = (amount * 0.10) if mode == "Cash" else 0
            save_db(db); return {"status": "Success"}
    return {"status": "Error"}@app.post("/clear-ledger/{worker_phone}")
def clear_ledger(worker_phone: str):
    db = get_db()
    for job in db["bookings"]:
        # Jo jobs is worker ki hain aur Completed hain, unhe Settle kar do
        if job.get("assigned_to") == worker_phone and job.get("status") == "Completed":
            job["status"] = "Settled" # Status badalne se wo calculation se bahar ho jayega
    save_db(db)
    return {"status": "Success"}# --- YE WALA HISSA ADD KAREIN ---
@app.post("/clear-ledger/{worker_phone}")
def clear_ledger(worker_phone: str):
    db = get_db()
    found = False
    for job in db["bookings"]:
        # Agar worker ka phone match kare aur uska status Completed ho
        if job.get("assigned_to") == worker_phone and job.get("status") == "Completed":
            job["status"] = "Settled"  # Status badal kar Settled kar do
            found = True
            
    if found:
        save_db(db)
        return {"status": "Success", "message": "Hisab clear ho gaya!"}
    else:
        return {"status": "Error", "message": "Koi completed job nahi mili!"}