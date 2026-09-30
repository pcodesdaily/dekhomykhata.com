"use client"

import { AlertTriangle, CheckCircle2, FileText, Lock, Upload, X } from "lucide-react"
import Link from "next/link"
import { useRef, useState, type DragEvent } from "react"
import { toast } from "sonner"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { useTransactions } from "@/features/transactions/transactions-provider"
import { ApiError, api } from "@/lib/api"
import { cn } from "@/lib/utils"

import type { StatementSummary } from "./statements-view"

const MAX_BYTES = 20 * 1024 * 1024
const ACCEPTED = [".pdf", ".csv"]

function validate(file: File): string | null {
  const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase()
  if (!ACCEPTED.includes(ext)) return "Choose a PDF or CSV bank statement."
  if (file.size > MAX_BYTES) return "This file is larger than 20 MB. Download a shorter date range from your bank."
  if (file.size === 0) return "This file is empty. Download the statement again from your bank."
  return null
}

const sizeLabel = (bytes: number) =>
  bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`

export function StatementUpload({ onUploaded }: { onUploaded: (summary: StatementSummary) => void }) {
  const { reload } = useTransactions()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<StatementSummary | null>(null)

  function choose(next: File | undefined) {
    if (!next) return
    const problem = validate(next)
    setError(problem)
    setFile(problem ? null : next)
    setResult(null)
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault()
    setDragging(false)
    choose(event.dataTransfer.files[0])
  }

  function reset() {
    setFile(null)
    setPassword("")
    setError(null)
    if (inputRef.current) inputRef.current.value = ""
  }

  async function upload() {
    if (!file) return
    setBusy(true)
    setError(null)
    const body = new FormData()
    body.append("file", file)
    if (password) body.append("password", password)
    try {
      const summary = await api<StatementSummary>("/statements", { method: "POST", body })
      setResult(summary)
      onUploaded(summary)
      reset()
      await reload()
      toast.success(`${summary.added} transactions added`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not read this statement.")
    } finally {
      setBusy(false)
    }
  }

  const pdf = file?.name.toLowerCase().endsWith(".pdf")
  const skipped = result ? result.rows - result.added : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload a statement</CardTitle>
        <CardDescription>Digital PDF or CSV export from your bank, up to 20 MB.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <label
          htmlFor="statement-file"
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors hover:border-primary/60 hover:bg-accent/40 has-[:focus-visible]:ring-3 has-[:focus-visible]:ring-ring/50",
            dragging && "border-primary bg-accent/50",
            busy && "pointer-events-none opacity-60",
          )}
        >
          <Upload className="size-6 text-primary" aria-hidden />
          <span className="font-medium">Drop your statement here or choose a file</span>
          <span className="text-sm text-muted-foreground">PDF or CSV · SBI, HDFC, ICICI, Axis, Kotak and most other banks</span>
          <input
            ref={inputRef}
            id="statement-file"
            name="statement"
            type="file"
            accept=".pdf,.csv,application/pdf,text/csv"
            className="sr-only"
            disabled={busy}
            onChange={(e) => choose(e.target.files?.[0])}
          />
        </label>

        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}

        {file && (
          <div className="flex items-center gap-3 rounded-lg border p-3">
            <FileText className="size-5 shrink-0 text-muted-foreground" aria-hidden />
            <div className="flex min-w-0 flex-1 flex-col">
              <span className="truncate text-sm font-medium">{file.name}</span>
              <span className="text-xs text-muted-foreground">{sizeLabel(file.size)}</span>
            </div>
            <Button variant="ghost" size="icon" onClick={reset} disabled={busy} aria-label="Remove file">
              <X aria-hidden />
            </Button>
          </div>
        )}

        {file && pdf && (
          <Field>
            <FieldLabel htmlFor="statement-password">PDF password (if any)</FieldLabel>
            <Input
              id="statement-password"
              name="statement-password"
              type="password"
              autoComplete="off"
              spellCheck={false}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={busy}
            />
            <FieldDescription>Banks often use your date of birth or part of your PAN. It is used once and never stored.</FieldDescription>
          </Field>
        )}

        {busy && (
          <div className="flex flex-col gap-2" aria-live="polite">
            <span className="text-sm">Reading and categorising your statement…</span>
            <Skeleton className="h-2 w-full rounded-full" />
          </div>
        )}

        {result && (
          <Alert>
            {result.balance_failures ? <AlertTriangle aria-hidden /> : <CheckCircle2 aria-hidden />}
            <AlertTitle>{result.filename}</AlertTitle>
            <AlertDescription>
              <p>
                Read {result.rows} transactions and added {result.added}
                {skipped > 0 && ` (${skipped} were already in your account)`}. {Math.round((result.categorised / Math.max(result.rows, 1)) * 100)}%
                were categorised automatically.
              </p>
              {result.balance_failures > 0 && (
                <p>{result.balance_failures} rows don’t match the running balance. Check them in Transactions.</p>
              )}
              <Link href="/dashboard" className="font-medium text-primary underline-offset-4 hover:underline">
                See your dashboard
              </Link>
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
      <CardFooter className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <span className="flex items-center gap-2 text-xs text-muted-foreground">
          <Lock className="size-3.5" aria-hidden /> Read on your MyKhata server. Nothing is sent to outside AI services.
        </span>
        <Button onClick={upload} disabled={!file || busy}>
          {busy ? "Reading…" : "Read statement"}
        </Button>
      </CardFooter>
    </Card>
  )
}
