import type { Metadata } from "next"

import { InsightsView } from "./_components/insights-view"

export const metadata: Metadata = { title: "AI insights" }

export default function InsightsPage() {
  return <InsightsView />
}
