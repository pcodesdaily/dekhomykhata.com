"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react"

import { api } from "@/lib/api"
import type { CategoryId, Transaction } from "@/lib/finance/types"

export type Budgets = Partial<Record<CategoryId, number>>
type Status = "loading" | "ready" | "error"

interface ApiTransaction extends Omit<Transaction, "balanceOk"> {
  balance_ok: boolean | null
}

export type NewTransaction = Pick<Transaction, "date" | "narration" | "type" | "amount"> &
  Partial<Pick<Transaction, "category" | "note">>

interface TransactionsContextValue {
  transactions: Transaction[]
  budgets: Budgets
  status: Status
  latestMonth: string
  reload: () => Promise<void>
  add: (transaction: NewTransaction) => Promise<Transaction>
  update: (id: string, changes: Partial<NewTransaction>) => Promise<Transaction>
  remove: (id: string) => Promise<void>
  clear: () => Promise<void>
  setBudget: (category: CategoryId, amount: number | null) => Promise<void>
}

const TransactionsContext = createContext<TransactionsContextValue | null>(null)

const fromApi = ({ balance_ok, ...t }: ApiTransaction): Transaction => ({ ...t, balanceOk: balance_ok })
const byDateDesc = (a: Transaction, b: Transaction) => b.date.localeCompare(a.date)

interface Loaded {
  rows: ApiTransaction[]
  limits: Budgets
}

async function fetchAll(): Promise<Loaded | null> {
  try {
    const [rows, limits] = await Promise.all([api<ApiTransaction[]>("/transactions"), api<Budgets>("/budgets")])
    return { rows, limits }
  } catch {
    return null
  }
}

export function TransactionsProvider({ children }: { children: ReactNode }) {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [budgets, setBudgets] = useState<Budgets>({})
  const [status, setStatus] = useState<Status>("loading")

  const apply = useCallback((data: Loaded | null) => {
    if (!data) return setStatus("error")
    setTransactions(data.rows.map(fromApi))
    setBudgets(data.limits)
    setStatus("ready")
  }, [])

  const reload = useCallback(() => fetchAll().then(apply), [apply])

  useEffect(() => {
    let cancelled = false
    fetchAll().then((data) => {
      if (!cancelled) apply(data)
    })
    return () => {
      cancelled = true
    }
  }, [apply])

  const value = useMemo<TransactionsContextValue>(() => {
    const latestMonth = transactions.reduce((max, t) => (t.date > max ? t.date : max), "").slice(0, 7)
    return {
      transactions,
      budgets,
      status,
      latestMonth,
      reload,
      add: async (input) => {
        const created = fromApi(await api<ApiTransaction>("/transactions", { method: "POST", json: input }))
        setTransactions((rows) => [created, ...rows].sort(byDateDesc))
        return created
      },
      update: async (id, changes) => {
        const updated = fromApi(await api<ApiTransaction>(`/transactions/${id}`, { method: "PATCH", json: changes }))
        setTransactions((rows) => rows.map((t) => (t.id === id ? updated : t)).sort(byDateDesc))
        return updated
      },
      remove: async (id) => {
        await api(`/transactions/${id}`, { method: "DELETE" })
        setTransactions((rows) => rows.filter((t) => t.id !== id))
      },
      clear: async () => {
        await api("/auth/me/data", { method: "DELETE" })
        setTransactions([])
        setBudgets({})
      },
      setBudget: async (category, amount) => {
        if (amount === null) await api(`/budgets/${category}`, { method: "DELETE" })
        else await api(`/budgets/${category}`, { method: "PUT", json: { amount } })
        setBudgets((current) => {
          const next = { ...current }
          if (amount === null) delete next[category]
          else next[category] = amount
          return next
        })
      },
    }
  }, [transactions, budgets, status, reload])

  return <TransactionsContext.Provider value={value}>{children}</TransactionsContext.Provider>
}

export function useTransactions() {
  const context = useContext(TransactionsContext)
  if (!context) throw new Error("useTransactions must be used inside <TransactionsProvider>")
  return context
}
