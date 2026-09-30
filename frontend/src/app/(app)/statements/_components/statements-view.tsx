"use client"

import { useCallback, useEffect, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { api } from "@/lib/api"
import { formatDate } from "@/lib/finance/format"

import { StatementUpload } from "./statement-upload"

export interface StatementSummary {
  id: number
  filename: string
  period_start: string | null
  period_end: string | null
  rows: number
  added: number
  categorised: number
  balance_failures: number
}

const TIPS = [
  "Download the statement from net banking or your bank’s app as a PDF or CSV, not a photo or scan.",
  "One file can cover up to a year. Shorter ranges upload faster.",
  "If the PDF asks for a password, enter it here. It is used once to open the file.",
  "Uploading overlapping statements is fine: transactions already in your account are skipped.",
]

export function StatementsView() {
  const [history, setHistory] = useState<StatementSummary[] | null>(null)

  const load = useCallback(() => {
    api<StatementSummary[]>("/statements").then(setHistory).catch(() => setHistory([]))
  }, [])

  useEffect(load, [load])

  return (
    <>
      <div className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <StatementUpload onUploaded={load} />
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Getting the right file</CardTitle>
            <CardDescription>What works best</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="flex list-disc flex-col gap-2 pl-4 text-sm text-muted-foreground">
              {TIPS.map((tip) => (
                <li key={tip}>{tip}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Uploaded statements</CardTitle>
          <CardDescription>Newest first</CardDescription>
        </CardHeader>
        <CardContent>
          {history === null ? (
            <Skeleton className="h-32 w-full" />
          ) : history.length ? (
            <div className="overflow-hidden rounded-lg border">
              <Table>
                <TableHeader className="bg-muted/50">
                  <TableRow>
                    <TableHead>File</TableHead>
                    <TableHead>Period</TableHead>
                    <TableHead className="text-right">Read</TableHead>
                    <TableHead className="text-right">Added</TableHead>
                    <TableHead className="text-right">Categorised</TableHead>
                    <TableHead>Balance check</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {history.map((row) => (
                    <TableRow key={row.id}>
                      <TableCell className="max-w-[28ch] truncate font-mono text-xs" title={row.filename}>
                        {row.filename}
                      </TableCell>
                      <TableCell className="whitespace-nowrap">
                        {row.period_start && row.period_end
                          ? `${formatDate(row.period_start, { day: "numeric", month: "short" })} – ${formatDate(row.period_end)}`
                          : "—"}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{row.rows}</TableCell>
                      <TableCell className="text-right tabular-nums">{row.added}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        {Math.round((row.categorised / Math.max(row.rows, 1)) * 100)}%
                      </TableCell>
                      <TableCell>
                        {row.balance_failures ? (
                          <Badge variant="outline" className="text-amber-700 dark:text-amber-400">
                            {row.balance_failures} rows to check
                          </Badge>
                        ) : (
                          <Badge variant="secondary">All rows match</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <Empty className="py-6">
              <EmptyHeader>
                <EmptyTitle>No statements yet</EmptyTitle>
                <EmptyDescription>Your uploads will be listed here.</EmptyDescription>
              </EmptyHeader>
            </Empty>
          )}
        </CardContent>
      </Card>
    </>
  )
}
