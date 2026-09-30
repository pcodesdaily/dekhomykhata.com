# MyKhata

**Apne paise ka poora hisaab.** MyKhata is a personal finance app for Indian bank statements. You upload your bank statement (PDF or CSV), and it shows you where your money went:

- **Cash flow:** how much came in, how much went out and how much you saved, every month
- **Spending:** every rupee sorted into 26 categories (Food & Dining, Rent, EMI & Loans, Shopping and more)
- **Budgets:** set a monthly limit per category and see where you spent too much or too little
- **Savings:** your savings rate every month, and the 50/30/20 check
- **Insights:** double payments, unusually big spends, price hikes
- **Recurring:** all your EMIs, SIPs, rent and subscriptions, with the next due date
- **Private:** everything runs on your own computer, and nothing is sent to outside AI services

## Watch the video

[![Watch the MyKhata promo video]([videos/mykhata-promo-horizontal.jpg](https://github.com/user-attachments/assets/72805593-f21e-425c-843c-afc64e704d72
))](videos/mykhata-promo-horizontal.mp4)

Click the picture to watch the video (1:44). A vertical version for phones is in [videos/mykhata-promo-vertical.mp4](videos/mykhata-promo-vertical.mp4).

---

## How to run it on your computer

MyKhata has two parts, and both run on your own computer:

| Part | Folder | What it does | Address |
|---|---|---|---|
| Backend | `backend/` | Reads statements, sorts transactions, stores your data | http://127.0.0.1:8000 |
| Website | `frontend/` | The dashboard you open in your browser | http://localhost:3000 |

You need two terminal windows: one for the backend and one for the website.

### What you need first

Install these once:

1. **Python 3.12** from https://www.python.org/downloads/. It must be version 3.12; 3.13 won't work yet.
2. **Node.js 22** (LTS) from https://nodejs.org/
3. **Git** from https://git-scm.com/downloads

To check they are installed, open a terminal and run `python --version`, `node --version` and `git --version`.

### Step 1: Download the project

```bash
git clone https://github.com/pcodesdaily/dekhomykhata.com.git
```

```bash
cd dekhomykhata.com
```

### Step 2: Set up the backend (one time only)

Go into the backend folder:

```bash
cd backend
```

Create a Python environment. On Windows, if `python` is not version 3.12, use `py -3.12` instead of `python`:

```bash
python -m venv .venv
```

Install the packages:

```bash
.venv/Scripts/python -m pip install -r requirements.lock.txt
```

```bash
.venv/Scripts/python -m pip install -e ".[dev]" --no-deps
```

> **On Mac or Linux**, write `.venv/bin/python` everywhere you see `.venv/Scripts/python`.

The trained model (`backend/artifacts/model.mkm`) is already included, so you don't need to train anything.

### Step 3: Create your login (one time only)

MyKhata has one owner, so there is no sign-up page. Create your login from the terminal (still inside `backend/`):

```bash
.venv/Scripts/python scripts/account.py you@example.com --name "Your Name"
```

It asks you to type a password twice (8 to 128 characters). Forgot it later? Run the same command again to set a new one.

### Step 4: Start the backend

Still inside `backend/`, run:

```bash
.venv/Scripts/python -m uvicorn mykhata_api.main:app --host 127.0.0.1 --port 8000
```

Keep this terminal open. The backend is running when you see `Uvicorn running on http://127.0.0.1:8000`.

### Step 5: Set up and start the website

Open a **second terminal**, go to the project folder, then into `frontend/`:

```bash
cd frontend
```

Install the packages (one time only):

```bash
npm install
```

Start the website:

```bash
npm run dev
```

Keep this terminal open too.

### Step 6: Use it

1. Open **http://localhost:3000** in your browser.
2. Log in with the email and password from Step 3.
3. Go to **Statements** and upload your bank statement.
   - Download it from net banking or your bank's app as a **PDF or CSV**, not a photo.
   - SBI, HDFC, ICICI, Axis, Kotak and most other banks work.
   - If the PDF has a password, type it in the box. It is only used to open the file and is never saved.
   - Want to try it first? Upload `bank_statement.pdf` from the project folder. It is a sample statement with fake data.
4. Open the **Dashboard** to see where your money went. Then try **Budgets**, **Recurring** and **AI insights**.

### Next time

You only need Step 4 (backend) and Step 5's `npm run dev` (website), each in its own terminal, then open http://localhost:3000.

To stop MyKhata, press `Ctrl + C` in both terminals.

---

## Your data

- Everything is saved in one file on your computer: `backend/data/app.db`. It is never uploaded to GitHub.
- To back up your transactions, use **Settings → Export CSV** (open Settings from your name at the bottom left).
- To start fresh, use **Settings → Delete all data**, or stop the backend and delete `backend/data/app.db`.

## If something goes wrong

| Problem | Fix |
|---|---|
| `python` is not 3.12 | Install Python 3.12 and use `py -3.12 -m venv .venv` (Windows) or `python3.12 -m venv .venv` (Mac/Linux) |
| The website says it can't reach the server | Make sure the backend terminal from Step 4 is still running |
| `Address already in use` or port 8000/3000 busy | Another copy is already running. Close it, or restart your computer |
| Forgot your password | Run the Step 3 command again with the same email |
| Changed backend code but nothing changed | Stop the backend with `Ctrl + C` and start it again (Step 4) |
| A statement won't upload | Use the digital PDF or CSV from net banking (not a scan), under 20 MB |

## More details

- [backend/README.md](backend/README.md): how the model was trained, accuracy, API and security
- [frontend/README.md](frontend/README.md): how the website is built and its folder layout
