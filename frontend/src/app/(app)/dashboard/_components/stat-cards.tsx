"use client"

import { Minus, TrendingDown, TrendingUp } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardAction, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { useTransactions } from "@/features/transactions/transactions-provider"
import { change, monthlySummary, type MonthSummary } from "@/lib/finance/analytics"
import { formatINR, formatMonth, formatPercent } from "@/lib/finance/format"
import { cn } from "@/lib/utils"

interface Stat {
  key: keyof Pick<MonthSummary, "moneyIn" | "spending" | "savings" | "invested">
  label: string
  goodWhenUp: boolean
  footer: (m: MonthSummary) => string
}

const STATS: Stat[] = [
  { key: "moneyIn", label: "Money in", goodWhenUp: true, footer: (m) => `${formatINR(m.income)} identified as income` },
  { key: "spending", label: "Spending", goodWhenUp: false, footer: (m) => `Needs ${formatINR(m.needs)} · Wants ${formatINR(m.wants)}` },
  {
    key: "savings",
    label: "Saved",
    goodWhenUp: true,
    footer: (m) => (m.savingsRate == null ? "No money came in" : `${formatPercent(m.savingsRate)} of money in`),
  },
  { key: "invested", label: "Invested", goodWhenUp: true, footer: () => "SIPs, deposits and other investments" },
]

export function StatCards() {
  const { transactions, latestMonth } = useTransactions()
  const months = monthlySummary(transactions)
  const index = months.findIndex((m) => m.month === latestMonth)
  const current = months[index]
  const previous = months[index - 1]
  if (!current) return null

  return (
    <section aria-labelledby="month-heading" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="month-heading" className="text-lg font-semibold text-balance">{formatMonth(current.month, { month: "long", year: "numeric" })}</h2>
        {previous && <p className="text-sm text-muted-foreground">Compared with {formatMonth(previous.month, { month: "long" })}</p>}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {STATS.map((stat) => {
          const delta = change(current[stat.key], previous?.[stat.key])
          const flat = delta !== null && Math.abs(delta) < 0.005
          const good = delta !== null && (delta >= 0) === stat.goodWhenUp
          const Icon = flat ? Minus : delta !== null && delta < 0 ? TrendingDown : TrendingUp
          return (
            <Card key={stat.key} className="@container/card gap-3">
              <CardHeader>
                <CardDescription>{stat.label}</CardDescription>
                <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
                  {formatINR(current[stat.key])}
                </CardTitle>
                {delta !== null && (
                  <CardAction>
                    <Badge variant="outline" className={cn(!flat && (good ? "text-emerald-700 dark:text-emerald-400" : "text-red-700 dark:text-red-400"))}>
                      <Icon aria-hidden />
                      <span className="sr-only">{flat ? "No change" : delta >= 0 ? "Up" : "Down"} vs last month: </span>
                      {flat ? "No change" : formatPercent(Math.abs(delta))}
                    </Badge>
                  </CardAction>
                )}
              </CardHeader>
              <CardFooter className="text-sm text-muted-foreground">{stat.footer(current)}</CardFooter>
            </Card>
          )
        })}
      </div>
    </section>
  )
}
