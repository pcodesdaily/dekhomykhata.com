"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useTransactions } from "@/features/transactions/transactions-provider"
import { budgetSplit, monthlySummary } from "@/lib/finance/analytics"
import { formatMonth, formatPercent } from "@/lib/finance/format"
import { cn } from "@/lib/utils"

export function BudgetSplitCard() {
  const { transactions, latestMonth } = useTransactions()
  const month = monthlySummary(transactions).find((m) => m.month === latestMonth)
  const split = month ? budgetSplit(month) : null

  return (
    <Card>
      <CardHeader>
        <CardTitle>50/30/20 check</CardTitle>
        <CardDescription>Share of money in, {formatMonth(latestMonth)}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        {split ? (
          split.map((row) => {
            const offTarget = row.over ? row.share > row.target : row.share < row.target
            return (
              <div key={row.key} className="flex flex-col gap-2">
                <div className="flex items-baseline justify-between text-sm">
                  <span className="font-medium">{row.label}</span>
                  <span className="tabular-nums">
                    <span className={cn("font-semibold", offTarget && "text-red-700 dark:text-red-400")}>
                      {formatPercent(row.share)}
                    </span>
                    <span className="text-muted-foreground">
                      {" "}
                      / {row.over ? "max" : "min"} {formatPercent(row.target)}
                    </span>
                  </span>
                </div>
                <Progress
                  value={Math.max(0, Math.min(100, row.share * 100))}
                  aria-label={`${row.label}: ${formatPercent(row.share)} of money in, target ${row.over ? "at most" : "at least"} ${formatPercent(row.target)}`}
                />
                <p className="text-xs text-muted-foreground">
                  {offTarget
                    ? row.over
                      ? `Above the ${formatPercent(row.target)} guideline`
                      : `Below the ${formatPercent(row.target)} guideline`
                    : "Within the guideline"}
                </p>
              </div>
            )
          })
        ) : (
          <p className="text-sm text-muted-foreground">No money came in this month, so the split can’t be worked out.</p>
        )}
      </CardContent>
    </Card>
  )
}
