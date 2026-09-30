import type { Metadata } from "next"

import { StatementsView } from "./_components/statements-view"

export const metadata: Metadata = { title: "Statements" }

export default function StatementsPage() {
  return <StatementsView />
}
