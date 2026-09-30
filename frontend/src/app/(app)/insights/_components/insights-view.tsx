"use client"

import { useState } from "react"
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, XAxis, YAxis } from "recharts"

import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { INSIGHT_KINDS, type InsightGroup } from "@/features/insights/insight-kinds"
import { InsightItem } from "@/features/insights/insight-item"
import { useTransactions } from "@/features/transactions/transactions-provider"
import { budgetSplit, insights, monthlySummary } from "@/lib/finance/analytics"
import { formatMonth, formatPercent } from "@/lib/finance/format"
import { cn } from "@/lib/utils"

const FILTERS: { value: "all" | InsightGroup; label: string }[] = [
  { value: "all", label: "All" },
  { value: "alert", label: "Alerts" },
  { value: "trend", label: "Trends" },
  { value: "saving", label: "Savings" },
]

const config = { rate: { label: "Savings rate", color: "var(--chart-1)" } } satisfies ChartConfig

export function InsightsView() {
  const { transactions, latestMonth } = useTransactions()
  const [filter, setFilter] = useState<"all" | InsightGroup>("all")
  const all = insights(transactions, latestMonth)
  const shown = filter === "all" ? all : all.filter((i) => INSIGHT_KINDS[i.kind].group === filter)
  const months = monthlySummary(transactions)
  const rates = months.map((m) => ({ month: m.month, rate: m.savingsRate ?? 0 }))

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>This month</CardTitle>
          <CardDescription>{formatMonth(latestMonth, { month: "long", year: "numeric" })} · {all.length} findings</CardDescription>
          <CardAction>
            <ToggleGroup type="single" variant="outline" size="sm" value={filter}
              onValueChange={(v) => v && setFilter(v as typeof filter)} aria-label="Filter insights">
              {FILTERS.map((f) => (
                <ToggleGroupItem key={f.value} value={f.value}>
                  {f.label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </CardAction>
        </CardHeader>
        <CardContent>
          {shown.length ? (
            <ul className="flex flex-col divide-y">
              {shown.map((item) => (
                <InsightItem key={item.id} insight={item} />
              ))}
            </ul>
          ) : (
            <Empty className="py-6">
              <EmptyHeader>
                <EmptyTitle>Nothing here this month</EmptyTitle>
                <EmptyDescription>Try another filter.</EmptyDescription>
              </EmptyHeader>
            </Empty>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Savings rate</CardTitle>
            <CardDescription>Share of money in that you kept. The line marks the 20% target.</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={config} className="aspect-auto h-64 w-full">
              <BarChart data={rates} margin={{ left: 4, right: 4 }}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="month" tickLine={false} axisLine={false} tickMargin={8}
                  tickFormatter={(v: string) => formatMonth(v, { month: "short" })} />
                <YAxis tickLine={false} axisLine={false} width={44} tickFormatter={(v: number) => formatPercent(v)} />
                <ChartTooltip cursor={false} content={<ChartTooltipContent
                  labelFormatter={(v) => formatMonth(String(v), { month: "long", year: "numeric" })}
                  formatter={(value) => <span className="font-medium tabular-nums">{formatPercent(Number(value))} saved</span>} />} />
                <ReferenceLine y={0.2} stroke="var(--muted-foreground)" strokeDasharray="4 4" />
                <Bar dataKey="rate" radius={4}>
                  {rates.map((r) => (
                    <Cell key={r.month} fill={r.rate < 0 ? "var(--chart-2)" : "var(--color-rate)"} />
                  ))}
                </Bar>
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>50/30/20 by month</CardTitle>
            <CardDescription>Needs (incl. EMIs), wants and savings as a share of money in</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-hidden rounded-lg border">
              <Table>
                <TableHeader className="bg-muted/50">
                  <TableRow>
                    <TableHead>Month</TableHead>
                    <TableHead className="text-right">Needs ≤ 50%</TableHead>
                    <TableHead className="text-right">Wants ≤ 30%</TableHead>
                    <TableHead className="text-right">Savings ≥ 20%</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[...months].reverse().map((m) => {
                    const split = budgetSplit(m)
                    return (
                      <TableRow key={m.month}>
                        <TableCell>{formatMonth(m.month)}</TableCell>
                        {split ? (
                          split.map((s) => {
                            const off = s.over ? s.share > s.target : s.share < s.target
                            return (
                              <TableCell key={s.key} className={cn("text-right tabular-nums", off && "font-semibold text-red-700 dark:text-red-400")}>
                                {formatPercent(s.share)}
                              </TableCell>
                            )
                          })
                        ) : (
                          <TableCell colSpan={3} className="text-muted-foreground">No money in</TableCell>
                        )}
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  )
}
