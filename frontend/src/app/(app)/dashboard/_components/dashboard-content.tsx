"use client"

import { FileUp, Plus, RefreshCw } from "lucide-react"
import Link from "next/link"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty"
import { TransactionFormDialog } from "@/features/transactions/transaction-form-dialog"
import { TransactionsTable } from "@/features/transactions/transactions-table"
import { useTransactions } from "@/features/transactions/transactions-provider"

import { BudgetSplitCard } from "./budget-split-card"
import { CashFlowChart } from "./cash-flow-chart"
import { CategorySpendChart } from "./category-spend-chart"
import { InsightsCard } from "./insights-card"
import { StatCards } from "./stat-cards"

export function DashboardContent() {
  const { transactions, status, reload } = useTransactions()
  const [adding, setAdding] = useState(false)

  if (status === "loading") {
    return (
      <div className="flex flex-col gap-6" aria-busy="true" aria-label="Loading your dashboard">
        <Skeleton className="h-7 w-48" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-36 rounded-xl" />
          ))}
        </div>
        <div className="grid gap-6 xl:grid-cols-3">
          <Skeleton className="h-96 rounded-xl xl:col-span-2" />
          <Skeleton className="h-96 rounded-xl" />
        </div>
      </div>
    )
  }

  if (status === "error") {
    return (
      <Empty className="flex-1 border border-dashed">
        <EmptyHeader>
          <EmptyTitle>Couldn’t load your data</EmptyTitle>
          <EmptyDescription>MyKhata’s server didn’t respond. Check that the API is running, then try again.</EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button onClick={() => void reload()}>
            <RefreshCw aria-hidden /> Try again
          </Button>
        </EmptyContent>
      </Empty>
    )
  }

  if (!transactions.length) {
    return (
      <Empty className="flex-1 border border-dashed">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <FileUp aria-hidden />
          </EmptyMedia>
          <EmptyTitle>No transactions yet</EmptyTitle>
          <EmptyDescription>Upload a bank statement or add a transaction to see your spending, savings and insights.</EmptyDescription>
        </EmptyHeader>
        <EmptyContent className="flex-row justify-center gap-2">
          <Button asChild>
            <Link href="/statements">
              <FileUp aria-hidden /> Upload statement
            </Link>
          </Button>
          <Button variant="outline" onClick={() => setAdding(true)}>
            <Plus aria-hidden /> Add transaction
          </Button>
        </EmptyContent>
        <TransactionFormDialog open={adding} onOpenChange={setAdding} />
      </Empty>
    )
  }

  return (
    <>
      <StatCards />
      <div className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <CashFlowChart />
        </div>
        <BudgetSplitCard />
      </div>
      <div className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <CategorySpendChart />
        </div>
        <InsightsCard />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Recent transactions</CardTitle>
          <CardDescription>Add, edit or delete. Changes update every chart above.</CardDescription>
        </CardHeader>
        <CardContent>
          <TransactionsTable />
        </CardContent>
      </Card>
    </>
  )
}
