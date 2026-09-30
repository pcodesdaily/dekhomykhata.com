import { CATEGORIES } from "./categories"
import { formatDate, formatINR, formatPercent } from "./format"
import { payeeName } from "./payee"
import type { Bucket, CategoryId, Insight, Transaction } from "./types"

// Same rules as backend/src/mykhata_ml/insights.py: savings follow the money, not the labels.
const SPEND_BUCKETS: Bucket[] = ["need", "want", "debt", "cash", "unknown"]

export interface MonthSummary {
  month: string
  moneyIn: number
  income: number
  spending: number
  needs: number
  wants: number
  debt: number
  invested: number
  savings: number
  savingsRate: number | null
}

export const monthOf = (tx: Transaction) => tx.date.slice(0, 7)

export function monthlySummary(transactions: Transaction[]): MonthSummary[] {
  const months = new Map<string, MonthSummary>()
  for (const tx of transactions) {
    if (tx.category === "SELF_TRANSFER") continue
    const key = monthOf(tx)
    const m = months.get(key) ?? {
      month: key, moneyIn: 0, income: 0, spending: 0, needs: 0, wants: 0, debt: 0, invested: 0, savings: 0, savingsRate: null,
    }
    const bucket = CATEGORIES[tx.category].bucket
    if (tx.type === "CREDIT") {
      if (tx.category === "REFUND_CASHBACK") m.spending -= tx.amount
      else m.moneyIn += tx.amount
      if (bucket === "income" && tx.category !== "REFUND_CASHBACK") m.income += tx.amount
      m.savings += tx.amount
    } else {
      m.savings -= tx.amount
      if (SPEND_BUCKETS.includes(bucket)) m.spending += tx.amount
      if (bucket === "need") m.needs += tx.amount
      if (bucket === "want") m.wants += tx.amount
      if (bucket === "debt") m.debt += tx.amount
      if (bucket === "saving") m.invested += tx.amount
    }
    months.set(key, m)
  }
  return [...months.values()]
    .map((m) => {
      const savings = m.savings + m.invested
      return { ...m, savings, savingsRate: m.moneyIn > 0 ? savings / m.moneyIn : null }
    })
    .sort((a, b) => a.month.localeCompare(b.month))
}

export function spendingByCategory(transactions: Transaction[], month?: string) {
  const totals = new Map<CategoryId, number>()
  for (const tx of transactions) {
    const bucket = CATEGORIES[tx.category].bucket
    if (tx.type !== "DEBIT" || !["need", "want", "debt"].includes(bucket)) continue
    if (month && monthOf(tx) !== month) continue
    totals.set(tx.category, (totals.get(tx.category) ?? 0) + tx.amount)
  }
  return [...totals.entries()]
    .map(([category, amount]) => ({ category, label: CATEGORIES[category].label, amount }))
    .sort((a, b) => b.amount - a.amount)
}

export function budgetSplit(m: MonthSummary) {
  if (m.moneyIn <= 0) return null
  return [
    { key: "needs", label: "Needs", share: (m.needs + m.debt) / m.moneyIn, target: 0.5, over: true },
    { key: "wants", label: "Wants", share: m.wants / m.moneyIn, target: 0.3, over: true },
    { key: "savings", label: "Savings", share: m.savings / m.moneyIn, target: 0.2, over: false },
  ] as const
}

export function change(current: number, previous: number | undefined): number | null {
  if (previous === undefined || previous === 0) return null
  return (current - previous) / Math.abs(previous)
}

const median = (values: number[]) => {
  const sorted = [...values].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2
}

const normalize = (narration: string) => narration.toLowerCase().replace(/\d+/g, "0")

export function insights(transactions: Transaction[], month: string): Insight[] {
  const out: Insight[] = []
  const debits = transactions.filter((t) => t.type === "DEBIT" && t.category !== "SELF_TRANSFER")
  const current = debits.filter((t) => monthOf(t) === month)

  for (const [category, rows] of groupBy(debits, (t) => t.category)) {
    if (rows.length < 6) continue
    const typical = median(rows.map((t) => t.amount))
    for (const t of rows.filter((r) => monthOf(r) === month && r.amount >= 1000 && r.amount > typical * 8)) {
      out.push({ id: `unusual-${t.id}`, kind: "unusual", category, amount: t.amount, title: "Unusually large payment",
        detail: `${formatINR(t.amount)} at ${payeeName(t.narration)} on ${formatDate(t.date, { day: "numeric", month: "short" })}, about ${Math.round(t.amount / typical)}× your usual ${CATEGORIES[category].label.toLowerCase()} payment.` })
    }
  }

  const byMonth = (category: CategoryId, key: string) =>
    debits.filter((t) => t.category === category && monthOf(t) === key).reduce((s, t) => s + t.amount, 0)
  const history = [...new Set(debits.map(monthOf))].filter((m) => m < month)
  if (history.length >= 2) {
    for (const category of new Set(current.map((t) => t.category))) {
      if (!["need", "want"].includes(CATEGORIES[category].bucket)) continue
      const now = byMonth(category, month)
      const typical = median(history.map((m) => byMonth(category, m)))
      if (typical <= 0 || Math.abs(now - typical) < 500) continue
      const ratio = now / typical
      if (ratio >= 1.25 || ratio <= 0.75) {
        const over = ratio > 1
        out.push({ id: `trend-${category}`, kind: over ? "overspend" : "underspend", category, amount: now,
          title: `${CATEGORIES[category].label} is ${over ? "up" : "down"}`,
          detail: `${formatINR(now)} this month against a typical ${formatINR(typical)}: ${
            ratio >= 2 ? `about ${Math.round(ratio)}× your usual month` : `${Math.round(Math.abs(ratio - 1) * 100)}% ${over ? "more" : "less"} than usual`}.` })
      }
    }
  }

  for (const [, rows] of groupBy(current, (t) => `${t.date}|${normalize(t.narration)}|${t.amount}`)) {
    if (rows.length > 1 && rows[0].category !== "OTHER") {
      out.push({ id: `double-${rows[0].id}`, kind: "double_charge", category: rows[0].category, amount: rows[0].amount,
        title: "Possible double charge", detail: `${rows.length} payments of ${formatINR(rows[0].amount)} to ${payeeName(rows[0].narration)} on ${formatDate(rows[0].date, { day: "numeric", month: "short" })}. Check you weren’t charged twice.` })
    }
  }

  for (const [, rows] of groupBy(debits, (t) => `${t.category}|${normalize(t.narration)}`)) {
    const sorted = [...rows].sort((a, b) => a.date.localeCompare(b.date))
    const last = sorted.at(-1)!
    if (sorted.length < 3 || monthOf(last) !== month) continue
    const typical = median(sorted.slice(0, -1).map((t) => t.amount))
    if (last.amount - typical >= 10 && last.amount / typical > 1.05 && sorted.slice(0, -1).every((t) => t.amount === typical)) {
      out.push({ id: `price-${last.id}`, kind: "price_change", category: last.category, amount: last.amount,
        title: `${payeeName(last.narration)} costs more now`, detail: `This regular payment went from ${formatINR(typical)} to ${formatINR(last.amount)}.` })
    }
  }

  const summary = monthlySummary(transactions).find((m) => m.month === month)
  if (summary?.savingsRate != null && summary.savingsRate < 0.2) {
    const overspent = summary.savingsRate < 0
    out.push({ id: "savings", kind: "savings", title: overspent ? "You spent more than came in" : "Savings below 20%",
      detail: overspent
        ? `Money out was ${formatPercent(-summary.savingsRate)} more than money in this month. The 50/30/20 rule suggests saving at least 20%.`
        : `You kept ${formatPercent(summary.savingsRate)} of the money that came in this month. The 50/30/20 rule suggests at least 20%.` })
  }
  const order: Insight["kind"][] = ["double_charge", "unusual", "overspend", "savings", "price_change", "underspend"]
  return out.sort((a, b) => order.indexOf(a.kind) - order.indexOf(b.kind))
}

export interface RecurringPayment {
  key: string
  narration: string
  category: CategoryId
  months: number
  typicalAmount: number
  lastAmount: number
  lastDate: string
  nextDate: string
  priceChange: boolean
}

const RECURRING_SKIP: CategoryId[] = ["OTHER", "TRANSFER_OUT", "SELF_TRANSFER", "CASH_WITHDRAWAL"]

export function recurringPayments(transactions: Transaction[]): RecurringPayment[] {
  const debits = transactions.filter((t) => t.type === "DEBIT" && !RECURRING_SKIP.includes(t.category))
  const out: RecurringPayment[] = []
  for (const [key, rows] of groupBy(debits, (t) => `${t.category}|${normalize(t.narration)}`)) {
    const sorted = [...rows].sort((a, b) => a.date.localeCompare(b.date))
    const months = new Set(sorted.map(monthOf)).size
    const amounts = sorted.map((t) => t.amount)
    const mean = amounts.reduce((s, a) => s + a, 0) / amounts.length
    const spread = Math.sqrt(amounts.reduce((s, a) => s + (a - mean) ** 2, 0) / amounts.length) / mean
    if (months < 3 || spread > 0.15) continue
    const last = sorted.at(-1)!
    const typical = median(amounts.slice(0, -1))
    const next = new Date(`${last.date}T00:00:00Z`)
    next.setUTCMonth(next.getUTCMonth() + 1)
    const diff = Math.abs(last.amount - typical)
    const earlier = amounts.slice(0, -1)
    const wasFixed = Math.max(...earlier) <= Math.min(...earlier) * 1.02
    out.push({
      key,
      narration: last.narration,
      category: last.category,
      months,
      typicalAmount: typical,
      lastAmount: last.amount,
      lastDate: last.date,
      nextDate: next.toISOString().slice(0, 10),
      priceChange: wasFixed && diff >= 10 && diff / typical > 0.05,
    })
  }
  return out.sort((a, b) => b.typicalAmount - a.typicalAmount)
}

export function typicalMonthlySpend(transactions: Transaction[], category: CategoryId, beforeMonth: string): number {
  const months = [...new Set(transactions.map(monthOf))].filter((m) => m < beforeMonth)
  if (!months.length) return 0
  return median(
    months.map((m) =>
      transactions
        .filter((t) => t.type === "DEBIT" && t.category === category && monthOf(t) === m)
        .reduce((s, t) => s + t.amount, 0),
    ),
  )
}

function groupBy<T, K>(rows: T[], key: (row: T) => K): Map<K, T[]> {
  const map = new Map<K, T[]>()
  for (const row of rows) map.set(key(row), [...(map.get(key(row)) ?? []), row])
  return map
}
