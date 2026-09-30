"use client"

import { AlertTriangle } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useTransactions } from "@/features/transactions/transactions-provider"
import { recurringPayments } from "@/lib/finance/analytics"
import { CATEGORIES } from "@/lib/finance/categories"
import { formatDate, formatINR } from "@/lib/finance/format"

export function RecurringView() {
  const { transactions } = useTransactions()
  const items = recurringPayments(transactions)
  const monthly = items.reduce((s, r) => s + r.lastAmount, 0)
  const changed = items.filter((r) => r.priceChange)

  return (
    <>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="gap-2">
          <CardHeader>
            <CardDescription>Committed every month</CardDescription>
            <CardTitle className="text-2xl tabular-nums">{formatINR(monthly)}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="gap-2">
          <CardHeader>
            <CardDescription>Recurring payments</CardDescription>
            <CardTitle className="text-2xl tabular-nums">{items.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="gap-2">
          <CardHeader>
            <CardDescription>Price changes this month</CardDescription>
            <CardTitle className="text-2xl tabular-nums">{changed.length}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Subscriptions, EMIs and regular payments</CardTitle>
          <CardDescription>Found automatically: the same payee at a steady amount in 3 or more months</CardDescription>
        </CardHeader>
        <CardContent>
          {items.length ? (
            <div className="overflow-hidden rounded-lg border">
              <Table>
                <TableHeader className="bg-muted/50">
                  <TableRow>
                    <TableHead>Payee</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Usual</TableHead>
                    <TableHead className="text-right">Latest</TableHead>
                    <TableHead className="text-right">Months</TableHead>
                    <TableHead>Next expected</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((r) => (
                    <TableRow key={r.key}>
                      <TableCell className="max-w-[30ch] truncate font-mono text-xs" title={r.narration}>
                        {r.narration}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{CATEGORIES[r.category].label}</Badge>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{formatINR(r.typicalAmount)}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        <span className="inline-flex items-center justify-end gap-1.5">
                          {r.priceChange && (
                            <AlertTriangle className="size-3.5 text-amber-700 dark:text-amber-400" aria-label="Price changed" />
                          )}
                          {formatINR(r.lastAmount)}
                        </span>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{r.months}</TableCell>
                      <TableCell className="whitespace-nowrap">{formatDate(r.nextDate, { day: "numeric", month: "short" })}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <Empty>
              <EmptyHeader>
                <EmptyTitle>No recurring payments found</EmptyTitle>
                <EmptyDescription>Upload at least 3 months of statements so regular payments can be spotted.</EmptyDescription>
              </EmptyHeader>
            </Empty>
          )}
        </CardContent>
      </Card>
    </>
  )
}
