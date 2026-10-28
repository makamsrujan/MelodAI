# PocketChange Insurance — Repository Setup

The dedicated repository name is intended to be `pocketchange-insurance`.

## Create the repository
1. Open https://github.com/new
2. Repository name: `pocketchange-insurance`
3. Description: `Hackathon prototype for explainable income disruption claims for gig workers`
4. Choose Public or Private according to your team's preference.
5. Do not initialize with a README, license, or `.gitignore` if you plan to push the prepared starter project as-is.
6. Create repository.

## Starter project architecture

```text
pocketchange-insurance/
├── frontend/                 # Next.js App Router + TypeScript + Tailwind
│   ├── app/
│   │   ├── page.tsx          # Worker dashboard; calls FastAPI
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   └── .env.example
├── backend/                  # FastAPI service
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py            # /health, /api/dashboard, /api/events
│   └── requirements.txt
├── .gitignore
└── README.md
```

## Push the prepared starter project
Download `pocketchange-insurance-starter.zip` from the ChatGPT conversation, extract it, and in a terminal at the extracted folder run:

```bash
git init
git add .
git commit -m "chore: initialize PocketChange Insurance prototype"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/pocketchange-insurance.git
git push -u origin main
```

Replace `<YOUR_USERNAME>` with your GitHub username. If Git reports that `origin` already exists, use `git remote set-url origin https://github.com/<YOUR_USERNAME>/pocketchange-insurance.git`.

## Local development

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`; the frontend uses the API at `http://localhost:8000` by default.

## Scope and safety
This is a fictional hackathon prototype. It does not provide actual insurance, accept premiums, or pay claims. Use synthetic data only. Before a production launch, restrict CORS, add authentication/authorization, persistent storage, audit logging, input validation, tests, and security/privacy review.
