"""Categories: direction, budget bucket (need/want/saving/debt/income/transfer/cash/unknown), real-world weight."""

CATEGORIES = {
    "FOOD_DINING":       {"label": "Food & Dining",        "direction": "DEBIT",  "bucket": "want",     "weight": 14},
    "GROCERIES":         {"label": "Groceries",            "direction": "DEBIT",  "bucket": "need",     "weight": 12},
    "SHOPPING":          {"label": "Shopping",             "direction": "DEBIT",  "bucket": "want",     "weight": 8},
    "TRANSPORT":         {"label": "Local Transport",      "direction": "DEBIT",  "bucket": "need",     "weight": 7},
    "FUEL":              {"label": "Fuel",                 "direction": "DEBIT",  "bucket": "need",     "weight": 4},
    "TRAVEL":            {"label": "Travel & Stays",       "direction": "DEBIT",  "bucket": "want",     "weight": 2},
    "BILLS_UTILITIES":   {"label": "Bills & Utilities",    "direction": "DEBIT",  "bucket": "need",     "weight": 5},
    "RENT":              {"label": "Rent",                 "direction": "DEBIT",  "bucket": "need",     "weight": 1},
    "ENTERTAINMENT":     {"label": "Entertainment",        "direction": "DEBIT",  "bucket": "want",     "weight": 3},
    "HEALTH":            {"label": "Health & Medical",     "direction": "DEBIT",  "bucket": "need",     "weight": 2},
    "EDUCATION":         {"label": "Education",            "direction": "DEBIT",  "bucket": "need",     "weight": 1},
    "PERSONAL_CARE":     {"label": "Personal Care & Fitness", "direction": "DEBIT", "bucket": "want",   "weight": 1},
    "INSURANCE":         {"label": "Insurance",            "direction": "DEBIT",  "bucket": "need",     "weight": 1},
    "BANK_CHARGES":      {"label": "Bank Charges & Fees",  "direction": "DEBIT",  "bucket": "need",     "weight": 1},
    "EMI_LOAN":          {"label": "EMI & Loans",          "direction": "DEBIT",  "bucket": "debt",     "weight": 2},
    "CREDIT_CARD_BILL":  {"label": "Credit Card Bill",     "direction": "DEBIT",  "bucket": "debt",     "weight": 1},
    "INVESTMENT":        {"label": "Investments",          "direction": "DEBIT",  "bucket": "saving",   "weight": 2},
    "CASH_WITHDRAWAL":   {"label": "Cash Withdrawal",      "direction": "DEBIT",  "bucket": "cash",     "weight": 2},
    "TRANSFER_OUT":      {"label": "Sent to People",       "direction": "DEBIT",  "bucket": "transfer", "weight": 10},
    "TRANSFER_IN":       {"label": "Received from People", "direction": "CREDIT", "bucket": "transfer", "weight": 6},
    "SELF_TRANSFER":     {"label": "Self Transfer / Cash Deposit", "direction": "BOTH", "bucket": "transfer", "weight": 2},
    "SALARY":            {"label": "Salary",               "direction": "CREDIT", "bucket": "income",   "weight": 1},
    "INTEREST":          {"label": "Interest",             "direction": "CREDIT", "bucket": "income",   "weight": 1},
    "INVESTMENT_RETURN": {"label": "Dividends & Redemptions", "direction": "CREDIT", "bucket": "income", "weight": 1},
    "REFUND_CASHBACK":   {"label": "Refunds & Cashback",   "direction": "CREDIT", "bucket": "income",   "weight": 2},
    "OTHER":             {"label": "Uncategorised",        "direction": "BOTH",   "bucket": "unknown",  "weight": 3},
}

CATEGORY_NAMES = list(CATEGORIES)
