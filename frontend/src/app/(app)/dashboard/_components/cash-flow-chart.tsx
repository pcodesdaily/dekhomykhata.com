"use client"

import { useState } from "react"
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { useTransactions } from "@/features/transactions/transactions-provider"
import { monthlySummary } from "@/lib/finance/analytics"
import { formatINR, formatINRCompact, formatMonth } from "@/lib/finance/format"

const config = {
  moneyIn: { label: "Money in", color: "var(--chart-1)" },
  spending: { label: "Spending", color: "var(--chart-2)" },
  savings: { label: "Saved", color: "var(--chart-3)" },
} satisfies ChartConfig

export function CashFlowChart() {
  const { transactions } = useTransactions()
  const [range, setRange] = useState("6")
  const data = monthlySummary(transactions).slice(-Number(range))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cash flow</CardTitle>
        <CardDescription>Money in, spending and what you kept each month</CardDescription>
        <CardAction>
          <ToggleGroup
            type="single"
            variant="outline"
            size="sm"
            value={range}
            onValueChange={(value) => value && setRange(value)}
            aria-label="Months to show"
          >
            <ToggleGroupItem value="3">3 months</ToggleGroupItem>
            <ToggleGroupItem value="6">6 months</ToggleGroupItem>
          </ToggleGroup>
        </CardAction>
      </CardHeader>
      <CardContent>
        <ChartContainer config={config} className="aspect-auto h-72 w-full">
          <BarChart data={data} margin={{ left: 4, right: 4 }} barGap={2}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="month" tickLine={false} axisLine={false} tickMargin={8} tickFormatter={(v: string) => formatMonth(v, { month: "short" })} />
            <YAxis tickLine={false} axisLine={false} width={52} tickFormatter={(v: number) => formatINRCompact(v)} />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  labelFormatter={(value) => formatMonth(String(value))}
                  formatter={(value, name) => (
                    <div className="flex w-full items-center justify-between gap-4">
                      <span className="text-muted-foreground">{config[name as keyof typeof config]?.label}</span>
                      <span className="font-medium tabular-nums">{formatINR(Number(value))}</span>
                    </div>
                  )}
                />
              }
            />
            <ChartLegend itemSorter={null} content={<ChartLegendContent />} />
            <Bar dataKey="moneyIn" fill="var(--color-moneyIn)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="spending" fill="var(--color-spending)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="savings" fill="var(--color-savings)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
