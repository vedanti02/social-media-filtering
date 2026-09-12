# Child Safety Messaging App — skeleton

## Backend
```
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Runs on http://localhost:8000 (docs at /docs).

### Seed dev data
With the venv active, from `backend/`:
```
python seed.py
```
Inserts one parent (id 1), one child, and six alerts with a mix of categories
and read states. Safe to re-run; it replaces the seed alerts each time.

## Frontend
```
cd frontend
npm install
npm run dev
```
Runs on http://localhost:5173. Requires Node 18+.
