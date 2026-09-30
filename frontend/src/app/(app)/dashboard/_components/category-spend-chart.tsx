"use client"

import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { useTransactions } from "@/features/transactions/transactions-provider"
import { spendingByCategory } from "@/lib/finance/analytics"
import { formatINR, formatMonth } from "@/lib/finance/format"

const TOP = 7

export function CategorySpendChart() {
  const { transactions, latestMonth } = useTransactions()
  const all = spendingByCategory(transactions, latestMonth)
  const total = all.reduce((sum, c) => sum + c.amount, 0)
  const rest = all.slice(TOP)
  const rows = [
    ...all.slice(0, TOP),
    ...(rest.length ? [{ category: "REST", label: `${rest.length} more categories`, amount: rest.reduce((s, c) => s + c.amount, 0) }] : []),
  ]
  const largest = Math.max(...rows.map((r) => r.amount), 1)

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Where the money went</CardTitle>
        <CardDescription>
          {formatMonth(latestMonth, { month: "long", year: "numeric" })} ·{" "}
          <span className="font-medium text-foreground tabular-nums">{formatINR(total)}</span> spent across {all.length} categories
        </CardDescription>
        <CardAction>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/transactions">View all</Link>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        {rows.length ? (
          <ol className="flex flex-col gap-3.5">
            {rows.map((row, i) => {
              const share = total ? row.amount / total : 0
              return (
                <li key={row.category} className="grid grid-cols-[1.5rem_1fr_auto] items-center gap-x-3 gap-y-1.5">
                  <span className="text-xs text-muted-foreground tabular-nums">{row.category === "REST" ? "…" : i + 1}</span>
                  <span className="truncate text-sm font-medium">{row.label}</span>
                  <span className="text-right text-sm tabular-nums">
                    <span className="font-semibold">{formatINR(row.amount)}</span>
                    <span className="ml-2 inline-block w-10 text-muted-foreground">{Math.round(share * 100)}%</span>
                  </span>
                  <div className="col-span-2 col-start-2 h-2 overflow-hidden rounded-full bg-muted" aria-hidden>
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.max((row.amount / largest) * 100, 2)}%`,
                        background: row.category === "REST" ? "var(--muted-foreground)" : "var(--chart-1)",
                        opacity: row.category === "REST" ? 0.35 : 1 - i * 0.08,
                      }}
                    />
                  </div>
                </li>
              )
            })}
          </ol>
        ) : (
          <p className="text-sm text-muted-foreground">No spending recorded this month yet.</p>
        )}
      </CardContent>
      <CardFooter className="text-sm text-muted-foreground">
        Spending only: investments, transfers and cash withdrawals are left out.
      </CardFooter>
    </Card>
  )
}
