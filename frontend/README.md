# MyKhata: frontend

The personal finance dashboard. Built with Next.js 16 (App Router, Turbopack), React 19, Tailwind CSS v4, shadcn/ui (radix-nova), Recharts 3, TanStack Table 9, react-hook-form and zod.

## Run

Node.js 20.9+ is required, and the API must be running (see `backend/README.md`). Run these from `frontend/`:

1. Install the packages:

   ```bash
   npm install
   ```

2. Start the dev server at http://localhost:3000:

   ```bash
   npm run dev
   ```

3. Lint the code:

   ```bash
   npm run lint
   ```

4. Make a production build:

   ```bash
   npm run build
   ```

`/api/*` is forwarded to the Python API (`API_URL`, default `http://127.0.0.1:8000`), so the login cookie stays first-party. `src/proxy.ts` sends signed-out visitors to `/login`, but the API checks the session on every request.

Theme: shadcn **Mist** base colour with a Tailwind **teal** accent (teal-700 buttons in light mode for AA contrast, teal-500 in dark), and a colour-blind-checked chart palette (teal, orange, blue).

## Layout
```
src/app/layout.tsx                 fonts, theme (light/dark/system), tooltips, toasts
src/app/(auth)/                    log in (single owner; no sign-up)
src/proxy.ts                       redirects signed-out visitors to /login
src/lib/api.ts                     fetch wrapper (CSRF header, errors, 401 → login)
src/app/(app)/layout.tsx           sidebar shell, session and data providers
src/app/(app)/dashboard/           cards, cash flow, 50/30/20, category spend, insights, recent transactions
src/app/(app)/transactions/        full transactions table (search, filter, sort, add/edit/delete)
src/app/(app)/statements/          PDF/CSV upload and statement history
src/app/(app)/budgets/             monthly limits per category, suggested from your typical month
src/app/(app)/recurring/           subscriptions, EMIs, rent and SIPs found automatically
src/app/(app)/insights/            all insights, savings-rate trend, 50/30/20 by month
src/app/(app)/model-report/        trained model stats (accuracy, comparison, confidence, categories, PDF reader)
src/app/(app)/settings/            profile, theme, categorisation, CSV export, delete all data (opened from the profile menu)
src/app/icon.svg, favicon.ico, apple-icon.png   app icons; src/components/logo.tsx and public/logo.svg for the logo
src/features/auth/                 session provider, login form
src/features/transactions/         API-backed store (transactions + budgets), table, dialogs, form schema
src/features/insights/             shared insight item and kinds
src/lib/finance/                   types, categories (mirror the backend), analytics, formatting
src/components/                    app sidebar, header, theme toggle; ui/ holds shadcn components
```

`src/lib/finance/analytics.ts` follows the same rules as `backend/src/mykhata_ml/insights.py`: savings follow the money (money in − money out + invested), plus 50/30/20, over/under spend against your median month, unusual payments, double charges and price changes.
