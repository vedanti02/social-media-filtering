# Child Safety Messaging App — skeleton

## Backend
```
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Runs on http://localhost:8000 (docs at /docs).

## Frontend
```
cd frontend
npm install
npm run dev
```
Runs on http://localhost:5173. Requires Node 18+.
