import type { Metadata } from "next"

import { BudgetsView } from "./_components/budgets-view"

export const metadata: Metadata = { title: "Budgets" }

export default function BudgetsPage() {
  return <BudgetsView />
}
