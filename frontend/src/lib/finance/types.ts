export type TxType = "DEBIT" | "CREDIT"

export type Bucket = "need" | "want" | "saving" | "debt" | "income" | "transfer" | "cash" | "unknown"

export type CategoryId =
  | "FOOD_DINING"
  | "GROCERIES"
  | "SHOPPING"
  | "TRANSPORT"
  | "FUEL"
  | "TRAVEL"
  | "BILLS_UTILITIES"
  | "RENT"
  | "ENTERTAINMENT"
  | "HEALTH"
  | "EDUCATION"
  | "PERSONAL_CARE"
  | "INSURANCE"
  | "BANK_CHARGES"
  | "EMI_LOAN"
  | "CREDIT_CARD_BILL"
  | "INVESTMENT"
  | "CASH_WITHDRAWAL"
  | "TRANSFER_OUT"
  | "TRANSFER_IN"
  | "SELF_TRANSFER"
  | "SALARY"
  | "INTEREST"
  | "INVESTMENT_RETURN"
  | "REFUND_CASHBACK"
  | "OTHER"

export interface Transaction {
  id: string
  date: string
  narration: string
  type: TxType
  amount: number
  category: CategoryId
  source: "statement" | "manual"
  confidence?: number | null
  note?: string | null
  balanceOk?: boolean | null
}

export type InsightKind = "overspend" | "underspend" | "unusual" | "double_charge" | "price_change" | "savings"

export interface Insight {
  id: string
  kind: InsightKind
  title: string
  detail: string
  amount?: number
  category?: CategoryId
}
