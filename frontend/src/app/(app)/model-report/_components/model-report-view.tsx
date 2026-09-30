"use client"

import { useEffect, useState } from "react"
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ApiError, api } from "@/lib/api"
import { CATEGORIES } from "@/lib/finance/categories"
import type { CategoryId } from "@/lib/finance/types"
import { cn } from "@/lib/utils"

interface Scores { accuracy: number; macro_f1: number }
interface Threshold { threshold: number; coverage: number; accuracy_answered: number }
interface ClassScore { precision: number; recall: number; "f1-score": number; support: number }
interface Approach { seen_accuracy: number; unseen_accuracy: number; seen_macro_f1: number; real_accuracy: number; abstains: boolean }

interface Results {
  data: { raw_rows: number; after_dropping_invalid: number; relabelled_ambiguous: number; after_dropping_duplicates: number; train_rows: number; test_rows: number }
  catalog: { brands: number; aliases: number }
  test_seen: Scores
  test_unseen: Scores
  cv_folds: (Scores & { fold: number })[]
  cv_mean: Scores
  thresholds_seen: Threshold[]
  thresholds_unseen: Threshold[]
  calibration_seen: { ece: number }
  calibration_unseen: { ece: number }
  counterparty_unseen: Record<string, { accuracy: number; rows: number }>
  per_class_seen: Record<string, ClassScore>
  per_class_unseen: Record<string, ClassScore>
  benchmark: Record<string, Approach>
  real: { rows: number; accuracy: number; informative_rows: number; informative_accuracy: number; opaque_kept_as_other: number }
  parser: Record<string, Record<string, number>>
  export: { bytes: number; features: number; microseconds_per_txn: number; agreement_with_full_precision: number }
}

const OURS = "MyKhata model"
const pct = (v: number, digits = 1) => `${(v * 100).toFixed(digits)}%`
const num = (v: number) => new Intl.NumberFormat("en-IN").format(v)

const chartConfig = {
  seen: { label: "Known brands", color: "var(--chart-1)" },
  unseen: { label: "Unseen brands", color: "var(--chart-2)" },
  real: { label: "Real statement", color: "var(--chart-3)" },
} satisfies ChartConfig

function Tile({ value, label, note }: { value: string; label: string; note: string }) {
  return (
    <Card className="gap-1">
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl tabular-nums">{value}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">{note}</CardContent>
    </Card>
  )
}

function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">{children}</CardContent>
    </Card>
  )
}

function DataTable({ head, rows, numericFrom = 1 }: { head: string[]; rows: React.ReactNode[][]; numericFrom?: number }) {
  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table>
        <TableHeader className="bg-muted/50">
          <TableRow>
            {head.map((h, i) => (
              <TableHead key={h} className={cn(i >= numericFrom && "text-right")}>{h}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, r) => (
            <TableRow key={r}>
              {row.map((cell, i) => (
                <TableCell key={i} className={cn(i >= numericFrom && "text-right tabular-nums")}>{cell}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

export function ModelReportView() {
  const [results, setResults] = useState<Results | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api<Results>("/model/results")
      .then(setResults)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load the model report."))
  }, [])

  if (error) {
    return (
      <Empty className="flex-1 border border-dashed">
        <EmptyHeader>
          <EmptyTitle>No model report</EmptyTitle>
          <EmptyDescription>{error}</EmptyDescription>
        </EmptyHeader>
      </Empty>
    )
  }
  if (!results) {
    return (
      <div className="flex flex-col gap-6" aria-busy="true" aria-label="Loading model report">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-32 rounded-xl" />)}
        </div>
        <Skeleton className="h-96 rounded-xl" />
      </div>
    )
  }

  const r = results
  const bench: Record<string, Approach> = {
    ...r.benchmark,
    [OURS]: { seen_accuracy: r.test_seen.accuracy, unseen_accuracy: r.test_unseen.accuracy, seen_macro_f1: r.test_seen.macro_f1,
      real_accuracy: r.real.accuracy, abstains: true },
  }
  const approaches = Object.entries(bench).sort((a, b) => b[1].seen_accuracy - a[1].seen_accuracy)
  const chartData = approaches.map(([name, a]) => ({ name, seen: a.seen_accuracy, unseen: a.unseen_accuracy, real: a.real_accuracy }))
  const atHalf = r.thresholds_seen.find((t) => t.threshold === 0.5) ?? r.thresholds_seen[0]
  const classes = (Object.keys(r.per_class_seen) as CategoryId[]).filter((c) => c in CATEGORIES)
    .sort((a, b) => r.per_class_seen[b]["f1-score"] - r.per_class_seen[a]["f1-score"])
  const layouts = Object.keys(r.parser)

  return (
    <>
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold text-balance">How the transaction categoriser performs</h2>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Every number comes from the last training run (<code className="font-mono">backend/scripts/train.py</code>).
          “Known brands” means new transactions from brands the model has seen; “unseen brands” means every brand in the
          test was hidden during training.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Tile value={pct(r.test_seen.accuracy)} label="Accuracy on known brands" note={`${num(r.catalog.brands)} Indian brands learnt`} />
        <Tile value={pct(r.real.accuracy)} label="Accuracy on a real statement" note={`${r.real.rows} hand-labelled transactions`} />
        <Tile value={pct(atHalf.accuracy_answered)} label="When it’s confident" note={`Labels ${pct(atHalf.coverage, 0)}; the rest stay “Uncategorised”`} />
        <Tile value={`${(r.export.bytes / 1e6).toFixed(1)} MB`} label="Model size" note={`${Math.round(r.export.microseconds_per_txn)} µs per transaction`} />
      </div>

      <Section title="Compared with other approaches" description="Same training and test data for every approach">
        <ChartContainer config={chartConfig} className="aspect-auto h-80 w-full">
          <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }} barGap={2}>
            <CartesianGrid horizontal={false} />
            <XAxis type="number" domain={[0, 1]} tickFormatter={(v: number) => pct(v, 0)} tickLine={false} axisLine={false} />
            <YAxis type="category" dataKey="name" width={190} tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
            <ChartTooltip cursor={false} content={<ChartTooltipContent formatter={(value, name) => (
              <div className="flex w-full justify-between gap-4">
                <span className="text-muted-foreground">{chartConfig[name as keyof typeof chartConfig]?.label}</span>
                <span className="font-medium tabular-nums">{pct(Number(value))}</span>
              </div>
            )} />} />
            <ChartLegend itemSorter={null} content={<ChartLegendContent />} />
            <Bar dataKey="seen" fill="var(--color-seen)" radius={3} barSize={9} />
            <Bar dataKey="unseen" fill="var(--color-unseen)" radius={3} barSize={9} />
            <Bar dataKey="real" fill="var(--color-real)" radius={3} barSize={9} />
          </BarChart>
        </ChartContainer>
        <DataTable
          head={["Approach", "Known brands", "Macro F1", "Unseen brands", "Real statement", "Can say “unsure”"]}
          rows={approaches.map(([name, a]) => [
            name === OURS ? <span className="font-semibold text-primary">{name}</span> : name,
            pct(a.seen_accuracy), pct(a.seen_macro_f1), pct(a.unseen_accuracy), pct(a.real_accuracy),
            a.abstains ? "Yes" : "No",
          ])}
        />
      </Section>

      <div className="grid gap-6 2xl:grid-cols-2">
        <Section title="Confidence you can trust"
          description={`Calibration error: ${pct(r.calibration_seen.ece)} on known brands, ${pct(r.calibration_unseen.ece)} on unseen`}>
          <DataTable
            head={["Threshold", "Known brands: labelled", "Known brands: accuracy", "Unseen: labelled", "Unseen: accuracy"]}
            rows={r.thresholds_seen.map((t, i) => [
              t.threshold === 0.5 ? <span className="font-semibold">{t.threshold} (default)</span> : t.threshold,
              pct(t.coverage), pct(t.accuracy_answered), pct(r.thresholds_unseen[i].coverage), pct(r.thresholds_unseen[i].accuracy_answered),
            ])}
          />
        </Section>
        <Section title="Where it is strong and weak" description="Unseen-brand test, by who is on the other side">
          <ul className="flex flex-col gap-4">
            {Object.entries(r.counterparty_unseen).sort((a, b) => b[1].accuracy - a[1].accuracy).map(([kind, v]) => (
              <li key={kind} className="flex flex-col gap-1.5">
                <div className="flex justify-between text-sm">
                  <span>{kind}</span>
                  <span className="tabular-nums"><span className="font-semibold">{pct(v.accuracy)}</span>
                    <span className="text-muted-foreground"> · {num(v.rows)} rows</span></span>
                </div>
                <Progress value={v.accuracy * 100} aria-label={`${kind}: ${pct(v.accuracy)}`} />
              </li>
            ))}
          </ul>
          <p className="text-sm text-muted-foreground">
            Brands the model has never seen are the weak spot. Adding them to the brand catalogue fixes it.
          </p>
        </Section>
      </div>

      <Section title="Every category" description="Precision, recall and F1 on known brands; F1 on unseen brands">
        <DataTable
          head={["Category", "Bucket", "Precision", "Recall", "F1", "F1 unseen", "Test rows"]}
          numericFrom={2}
          rows={classes.map((c) => {
            const s = r.per_class_seen[c]
            return [CATEGORIES[c].label, <Badge key={c} variant="secondary">{CATEGORIES[c].bucket}</Badge>, pct(s.precision), pct(s.recall),
              pct(s["f1-score"]), pct(r.per_class_unseen[c]?.["f1-score"] ?? 0), num(s.support)]
          })}
        />
      </Section>

      <div className="grid gap-6 xl:grid-cols-2">
        <Section title="Real bank statement" description={`${r.real.rows} transactions from a real, anonymised Indian account`}>
          <DataTable
            head={["Measure", "Result"]}
            rows={[
              ["All rows", pct(r.real.accuracy)],
              [`Rows whose text shows the category (${r.real.informative_rows})`, pct(r.real.informative_accuracy)],
              ["Opaque rows kept as “Uncategorised”", pct(r.real.opaque_kept_as_other)],
            ]}
          />
        </Section>
        <Section title="Reading statement PDFs" description="Tested on 50 statements with known answers">
          <DataTable
            head={["Field", ...layouts]}
            rows={[["Transactions found", "found"], ["Date", "date"], ["Amount", "amount"], ["Debit / credit", "type"],
              ["Balance", "balance"], ["Description", "narration_ignoring_spaces"]].map(([label, key]) => [
              label, ...layouts.map((l) => pct(r.parser[l][key] ?? 0)),
            ])}
          />
        </Section>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Section title="Stable across splits" description="Five-fold cross-validation with brands kept on one side">
          <DataTable
            head={["Fold", "Accuracy", "Macro F1"]}
            rows={[...r.cv_folds.map((f) => [`Fold ${f.fold}`, pct(f.accuracy), pct(f.macro_f1)]),
              [<span key="m" className="font-semibold">Mean</span>, pct(r.cv_mean.accuracy), pct(r.cv_mean.macro_f1)]]}
          />
        </Section>
        <Section title="Training data and model file">
          <DataTable
            head={["Item", "Value"]}
            rows={[
              ["Generated transactions", num(r.data.raw_rows)],
              ["After cleaning", num(r.data.after_dropping_duplicates)],
              ["Ambiguous texts relabelled “Uncategorised”", num(r.data.relabelled_ambiguous)],
              ["Brands / name variants", `${num(r.catalog.brands)} / ${num(r.catalog.aliases)}`],
              ["Features", num(r.export.features)],
              ["Same answer as full precision", pct(r.export.agreement_with_full_precision, 2)],
            ]}
          />
        </Section>
      </div>
    </>
  )
}
