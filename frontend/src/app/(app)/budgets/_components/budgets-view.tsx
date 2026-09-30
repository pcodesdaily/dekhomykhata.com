"use client"

import { Pencil, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useTransactions } from "@/features/transactions/transactions-provider"
import { ApiError } from "@/lib/api"
import { spendingByCategory, typicalMonthlySpend } from "@/lib/finance/analytics"
import { CATEGORIES, CATEGORY_IDS } from "@/lib/finance/categories"
import { formatINR, formatMonth } from "@/lib/finance/format"
import type { CategoryId } from "@/lib/finance/types"
import { cn } from "@/lib/utils"

const BUDGETABLE = CATEGORY_IDS.filter((id) => ["need", "want"].includes(CATEGORIES[id].bucket))

export function BudgetsView() {
  const { transactions, budgets, latestMonth, setBudget } = useTransactions()
  const [editing, setEditing] = useState<{ category?: CategoryId } | null>(null)
  const spent = new Map(spendingByCategory(transactions, latestMonth).map((c) => [c.category, c.amount]))
  const rows = (Object.entries(budgets) as [CategoryId, number][])
    .map(([category, limit]) => ({ category, limit, spent: spent.get(category) ?? 0 }))
    .sort((a, b) => b.spent / b.limit - a.spent / a.limit)
  const totalLimit = rows.reduce((s, r) => s + r.limit, 0)
  const totalSpent = rows.reduce((s, r) => s + r.spent, 0)
  const unbudgeted = [...spent.entries()].filter(([c]) => !budgets[c] && BUDGETABLE.includes(c))

  return (
    <>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { label: "Budgeted this month", value: formatINR(totalLimit) },
          { label: "Spent in these categories", value: formatINR(totalSpent) },
          {
            label: totalSpent > totalLimit ? "Over budget" : "Left to spend",
            value: formatINR(Math.abs(totalLimit - totalSpent)),
            warn: totalSpent > totalLimit,
          },
        ].map((tile) => (
          <Card key={tile.label} className="gap-2">
            <CardHeader>
              <CardDescription>{tile.label}</CardDescription>
              <CardTitle className={cn("text-2xl tabular-nums", tile.warn && "text-red-700 dark:text-red-400")}>{tile.value}</CardTitle>
            </CardHeader>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Monthly budgets</CardTitle>
          <CardDescription>{formatMonth(latestMonth, { month: "long", year: "numeric" })}</CardDescription>
          <CardAction>
            <Button onClick={() => setEditing({})}>
              <Plus aria-hidden /> Add budget
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent>
          {rows.length ? (
            <ul className="flex flex-col divide-y">
              {rows.map((row) => {
                const share = row.spent / row.limit
                const over = share > 1
                return (
                  <li key={row.category} className="flex flex-col gap-2 py-4 first:pt-0 last:pb-0">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{CATEGORIES[row.category].label}</span>
                        {over && (
                          <Badge variant="outline" className="text-red-700 dark:text-red-400">
                            Over by {formatINR(row.spent - row.limit)}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-sm tabular-nums">
                          <span className={cn("font-semibold", over && "text-red-700 dark:text-red-400")}>{formatINR(row.spent)}</span>
                          <span className="text-muted-foreground"> of {formatINR(row.limit)}</span>
                        </span>
                        <Button variant="ghost" size="icon" className="size-8" onClick={() => setEditing({ category: row.category })}
                          aria-label={`Edit ${CATEGORIES[row.category].label} budget`}>
                          <Pencil aria-hidden />
                        </Button>
                        <Button variant="ghost" size="icon" className="size-8"
                          onClick={() =>
                            setBudget(row.category, null)
                              .then(() => toast("Budget removed", {
                                action: { label: "Undo", onClick: () => void setBudget(row.category, row.limit).catch(() => toast.error("Could not restore it")) },
                              }))
                              .catch((error) => toast.error(error instanceof ApiError ? error.message : "Could not remove the budget"))
                          }
                          aria-label={`Remove ${CATEGORIES[row.category].label} budget`}>
                          <Trash2 aria-hidden />
                        </Button>
                      </div>
                    </div>
                    <Progress
                      value={Math.min(100, share * 100)}
                      className={cn(over && "[&>[data-slot=progress-indicator]]:bg-destructive")}
                      aria-label={`${CATEGORIES[row.category].label}: ${Math.round(share * 100)}% of budget used`}
                    />
                    <p className="text-xs text-muted-foreground">
                      {over ? `${Math.round(share * 100)}% of budget used` : `${formatINR(row.limit - row.spent)} left · ${Math.round(share * 100)}% used`}
                    </p>
                  </li>
                )
              })}
            </ul>
          ) : (
            <Empty>
              <EmptyHeader>
                <EmptyTitle>No budgets yet</EmptyTitle>
                <EmptyDescription>Set a monthly limit for a category to see how close you are.</EmptyDescription>
              </EmptyHeader>
              <EmptyContent>
                <Button onClick={() => setEditing({})}>
                  <Plus aria-hidden /> Add budget
                </Button>
              </EmptyContent>
            </Empty>
          )}
        </CardContent>
      </Card>

      {unbudgeted.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Spending without a budget</CardTitle>
            <CardDescription>Categories you spent on this month</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {unbudgeted.map(([category, amount]) => (
              <Button key={category} variant="outline" size="sm" onClick={() => setEditing({ category })}>
                <Plus aria-hidden /> {CATEGORIES[category].label} · {formatINR(amount)}
              </Button>
            ))}
          </CardContent>
        </Card>
      )}

      <BudgetDialog
        key={editing?.category ?? "new"}
        open={editing !== null}
        category={editing?.category}
        onOpenChange={(open) => !open && setEditing(null)}
      />
    </>
  )
}

function BudgetDialog({ open, category, onOpenChange }: { open: boolean; category?: CategoryId; onOpenChange: (open: boolean) => void }) {
  const { transactions, budgets, latestMonth, setBudget } = useTransactions()
  const [selected, setSelected] = useState<CategoryId | undefined>(category)
  const [amount, setAmount] = useState(category && budgets[category] ? String(budgets[category]) : "")
  const [error, setError] = useState<string | null>(null)
  const suggestion = selected ? Math.round(typicalMonthlySpend(transactions, selected, latestMonth) / 100) * 100 : 0

  const [saving, setSaving] = useState(false)

  async function save() {
    const value = Number(amount)
    if (!selected) return setError("Choose a category")
    if (!amount || !Number.isFinite(value) || value <= 0) return setError("Enter a monthly amount above ₹0")
    if (value > 1_00_00_000) return setError("Amount is too large")
    setSaving(true)
    try {
      await setBudget(selected, Math.round(value))
      toast.success(`${CATEGORIES[selected].label} budget saved`)
      onOpenChange(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save the budget")
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{category && budgets[category] ? "Edit budget" : "Add budget"}</DialogTitle>
          <DialogDescription>A monthly spending limit for one category.</DialogDescription>
        </DialogHeader>
        <form
          id="budget-form"
          className="flex flex-col gap-4"
          noValidate
          onSubmit={(e) => {
            e.preventDefault()
            void save()
          }}
        >
          <Field>
            <FieldLabel htmlFor="budget-category">Category</FieldLabel>
            <Select value={selected} onValueChange={(v) => setSelected(v as CategoryId)} disabled={Boolean(category)}>
              <SelectTrigger id="budget-category" className="w-full">
                <SelectValue placeholder="Choose a category" />
              </SelectTrigger>
              <SelectContent>
                {BUDGETABLE.filter((id) => id === category || !budgets[id]).map((id) => (
                  <SelectItem key={id} value={id}>
                    {CATEGORIES[id].label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field data-invalid={Boolean(error)}>
            <FieldLabel htmlFor="budget-amount">Monthly limit (₹)</FieldLabel>
            <Input
              id="budget-amount"
              name="budget-amount"
              inputMode="numeric"
              autoComplete="off"
              placeholder="e.g. 5000…"
              value={amount}
              onChange={(e) => {
                setAmount(e.target.value.replace(/[^\d.]/g, ""))
                setError(null)
              }}
              aria-invalid={Boolean(error)}
            />
            {suggestion > 0 && (
              <FieldDescription>
                Your typical month: {formatINR(suggestion)}.{" "}
                <button type="button" className="font-medium text-primary underline-offset-4 hover:underline" onClick={() => setAmount(String(suggestion))}>
                  Use this
                </button>
              </FieldDescription>
            )}
            {error && <FieldError>{error}</FieldError>}
          </Field>
        </form>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button type="submit" form="budget-form" disabled={saving}>
            {saving ? "Saving…" : "Save budget"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
