# MyKhata

A personal finance tracker for Indian bank statements. Upload a PDF or CSV statement, and every transaction is read,
categorised by a trained model into 26 categories, and turned into a dashboard: cash flow, savings, the 50/30/20 split,
budgets, recurring payments and insights such as unusual payments or double charges.

| Folder | What it is |
|---|---|
| [`backend/`](backend/README.md) | Python: model training, statement reader, insights and the FastAPI + SQLite API |
| [`frontend/`](frontend/README.md) | Next.js 16 + shadcn/ui dashboard |
| `bank_statement.pdf` | A sample statement (fictional bank and account) for trying the app |

## Run locally

1. Set up and start the API (see `backend/README.md` for first-time setup):

   ```bash
   cd backend && .venv/Scripts/python -m uvicorn mykhata_api.main:app --host 127.0.0.1 --port 8000
   ```

2. Create your login (one owner; there is no sign-up page):

   ```bash
   cd backend && .venv/Scripts/python scripts/account.py you@example.com --name "Your Name"
   ```

3. Start the website, then open http://localhost:3000:

   ```bash
   cd frontend && npm install && npm run dev
   ```

The model report (accuracy, comparison with other approaches, confidence) is in the app under **Model report**, and as a
standalone page in `backend/reports/report.html`.
