import type { Bucket, CategoryId, TxType } from "./types"

// Mirrors backend/src/mykhata_ml/categories.py
export const CATEGORIES: Record<CategoryId, { label: string; bucket: Bucket; direction: TxType | "BOTH" }> = {
  FOOD_DINING: { label: "Food & Dining", bucket: "want", direction: "DEBIT" },
  GROCERIES: { label: "Groceries", bucket: "need", direction: "DEBIT" },
  SHOPPING: { label: "Shopping", bucket: "want", direction: "DEBIT" },
  TRANSPORT: { label: "Local Transport", bucket: "need", direction: "DEBIT" },
  FUEL: { label: "Fuel", bucket: "need", direction: "DEBIT" },
  TRAVEL: { label: "Travel & Stays", bucket: "want", direction: "DEBIT" },
  BILLS_UTILITIES: { label: "Bills & Utilities", bucket: "need", direction: "DEBIT" },
  RENT: { label: "Rent", bucket: "need", direction: "DEBIT" },
  ENTERTAINMENT: { label: "Entertainment", bucket: "want", direction: "DEBIT" },
  HEALTH: { label: "Health & Medical", bucket: "need", direction: "DEBIT" },
  EDUCATION: { label: "Education", bucket: "need", direction: "DEBIT" },
  PERSONAL_CARE: { label: "Personal Care & Fitness", bucket: "want", direction: "DEBIT" },
  INSURANCE: { label: "Insurance", bucket: "need", direction: "DEBIT" },
  BANK_CHARGES: { label: "Bank Charges & Fees", bucket: "need", direction: "DEBIT" },
  EMI_LOAN: { label: "EMI & Loans", bucket: "debt", direction: "DEBIT" },
  CREDIT_CARD_BILL: { label: "Credit Card Bill", bucket: "debt", direction: "DEBIT" },
  INVESTMENT: { label: "Investments", bucket: "saving", direction: "DEBIT" },
  CASH_WITHDRAWAL: { label: "Cash Withdrawal", bucket: "cash", direction: "DEBIT" },
  TRANSFER_OUT: { label: "Sent to People", bucket: "transfer", direction: "DEBIT" },
  TRANSFER_IN: { label: "Received from People", bucket: "transfer", direction: "CREDIT" },
  SELF_TRANSFER: { label: "Self Transfer / Cash Deposit", bucket: "transfer", direction: "BOTH" },
  SALARY: { label: "Salary", bucket: "income", direction: "CREDIT" },
  INTEREST: { label: "Interest", bucket: "income", direction: "CREDIT" },
  INVESTMENT_RETURN: { label: "Dividends & Redemptions", bucket: "income", direction: "CREDIT" },
  REFUND_CASHBACK: { label: "Refunds & Cashback", bucket: "income", direction: "CREDIT" },
  OTHER: { label: "Uncategorised", bucket: "unknown", direction: "BOTH" },
}

export const CATEGORY_IDS = Object.keys(CATEGORIES) as CategoryId[]

export function categoriesFor(type: TxType): CategoryId[] {
  return CATEGORY_IDS.filter((id) => {
    const direction = CATEGORIES[id].direction
    return direction === "BOTH" || direction === type
  })
}
