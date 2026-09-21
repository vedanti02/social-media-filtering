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

Demo login: `parent@example.com` / `demo1234`. Or click "Create an account" on
the login page to sign up (a parent account plus a profile for one child).

> Auth added a `password_hash` column and an `authtoken` table. If you have an
> older local `backend/app.db`, delete it and re-run `python seed.py`.

## Frontend
```
cd frontend
npm install
npm run dev
```
Runs on http://localhost:5173. Requires Node 18+.
