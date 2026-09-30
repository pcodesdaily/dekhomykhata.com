import type { Metadata } from "next"

import { ModelReportView } from "./_components/model-report-view"

export const metadata: Metadata = { title: "Model report" }

export default function ModelReportPage() {
  return <ModelReportView />
}
