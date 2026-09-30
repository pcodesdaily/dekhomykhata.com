"use client"

import { Sparkles } from "lucide-react"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { InsightItem } from "@/features/insights/insight-item"
import { useTransactions } from "@/features/transactions/transactions-provider"
import { insights } from "@/lib/finance/analytics"

export function InsightsCard({ limit = 5 }: { limit?: number }) {
  const { transactions, latestMonth } = useTransactions()
  const items = insights(transactions, latestMonth)

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="size-4 text-primary" aria-hidden /> Insights
        </CardTitle>
        <CardDescription>What changed this month</CardDescription>
        <CardAction>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/insights">See all</Link>
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        {items.length ? (
          <ul className="flex flex-col divide-y">
            {items.slice(0, limit).map((item) => (
              <InsightItem key={item.id} insight={item} />
            ))}
          </ul>
        ) : (
          <Empty className="py-6">
            <EmptyHeader>
              <EmptyTitle>Nothing unusual this month</EmptyTitle>
              <EmptyDescription>Spending looks in line with your usual months.</EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
      </CardContent>
    </Card>
  )
}
