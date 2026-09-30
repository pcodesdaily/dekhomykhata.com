import type { Metadata } from "next"

import { Card, CardContent } from "@/components/ui/card"
import { TransactionsTable } from "@/features/transactions/transactions-table"

export const metadata: Metadata = { title: "Transactions" }

export default function TransactionsPage() {
  return (
    <Card>
      <CardContent>
        <TransactionsTable pageSize={15} />
      </CardContent>
    </Card>
  )
}
