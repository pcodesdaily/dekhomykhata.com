"use client"

import { Download, Monitor, Moon, Sun, Trash2 } from "lucide-react"
import { useTheme } from "next-themes"
import { useState, useSyncExternalStore } from "react"
import { toast } from "sonner"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Skeleton } from "@/components/ui/skeleton"
import { Slider } from "@/components/ui/slider"
import { useSession, type User } from "@/features/auth/session-provider"
import { useTransactions } from "@/features/transactions/transactions-provider"
import { ApiError, api } from "@/lib/api"
import { CATEGORIES } from "@/lib/finance/categories"
import type { Transaction } from "@/lib/finance/types"

const THEMES = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
]

function toCsv(rows: Transaction[]): string {
  const cell = (v: string | number) => {
    const s = String(v)
    const safe = /^[=+\-@]/.test(s) ? `'${s}` : s
    return /[",\n]/.test(safe) ? `"${safe.replaceAll('"', '""')}"` : safe
  }
  const head = ["date", "narration", "type", "amount", "category", "source"]
  const body = rows.map((t) => [t.date, t.narration, t.type, t.amount, CATEGORIES[t.category].label, t.source].map(cell).join(","))
  return [head.join(","), ...body].join("\n")
}

const subscribeNoop = () => () => {}

export function SettingsView() {
  const { user } = useSession()
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
      {user ? <AccountSettings key={user.id} user={user} /> : <Skeleton className="h-72 w-full rounded-xl" />}
      <AppearanceSettings />
      <DataSettings />
    </div>
  )
}

function AccountSettings({ user }: { user: User }) {
  const { setUser } = useSession()
  const [name, setName] = useState(user.name)
  const [threshold, setThreshold] = useState([user.confidence_threshold])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function save() {
    if (!name.trim()) return setError("Enter your name")
    setSaving(true)
    try {
      setUser(await api<User>("/auth/me", { method: "PATCH", json: { name: name.trim(), confidence_threshold: threshold[0] } }))
      setError(null)
      toast.success("Settings saved")
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not save your settings")
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Account</CardTitle>
        <CardDescription>Your details and how statements are categorised</CardDescription>
      </CardHeader>
      <CardContent>
        <form id="account-form" className="flex flex-col gap-6" noValidate onSubmit={(e) => { e.preventDefault(); void save() }}>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field data-invalid={Boolean(error)}>
              <FieldLabel htmlFor="profile-name">Name</FieldLabel>
              <Input id="profile-name" name="name" autoComplete="name" value={name} aria-invalid={Boolean(error)}
                onChange={(e) => { setName(e.target.value); setError(null) }} />
              {error && <FieldError>{error}</FieldError>}
            </Field>
            <Field>
              <FieldLabel htmlFor="profile-email">Email</FieldLabel>
              <Input id="profile-email" name="email" type="email" value={user.email} readOnly disabled />
            </Field>
          </div>
          <Field>
            <div className="flex items-center justify-between">
              <FieldLabel htmlFor="confidence">Minimum confidence for automatic categories</FieldLabel>
              <span className="text-sm font-medium tabular-nums">{Math.round(threshold[0] * 100)}%</span>
            </div>
            <Slider id="confidence" min={0.3} max={0.9} step={0.1} value={threshold} onValueChange={setThreshold}
              aria-label="Minimum confidence" />
            <FieldDescription>
              Below this, transactions are left as “Uncategorised” for you to review. At 50% the model is right about 98%
              of the time on brands it knows. Applies to statements you upload from now on.
            </FieldDescription>
          </Field>
        </form>
      </CardContent>
      <CardFooter className="justify-end">
        <Button type="submit" form="account-form" disabled={saving}>{saving ? "Saving…" : "Save changes"}</Button>
      </CardFooter>
    </Card>
  )
}

function AppearanceSettings() {
  const { theme, setTheme } = useTheme()
  const mounted = useSyncExternalStore(subscribeNoop, () => true, () => false)
  return (
    <Card>
      <CardHeader>
        <CardTitle>Appearance</CardTitle>
        <CardDescription>Choose a theme or follow your device</CardDescription>
      </CardHeader>
      <CardContent>
        <RadioGroup value={mounted ? theme : undefined} onValueChange={setTheme} className="grid grid-cols-3 gap-3" aria-label="Theme">
          {THEMES.map(({ value, label, icon: Icon }) => (
            <FieldLabel key={value} htmlFor={`theme-${value}`}
              className="flex w-full cursor-pointer flex-col items-center gap-2 rounded-lg border p-4 hover:bg-accent/50 has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/5 has-[:focus-visible]:ring-3 has-[:focus-visible]:ring-ring/50">
              <RadioGroupItem id={`theme-${value}`} value={value} className="sr-only" />
              <Icon className="size-5" aria-hidden />
              <span className="text-sm font-medium">{label}</span>
            </FieldLabel>
          ))}
        </RadioGroup>
      </CardContent>
    </Card>
  )
}

function DataSettings() {
  const { transactions, clear } = useTransactions()

  function exportCsv() {
    const url = URL.createObjectURL(new Blob([toCsv(transactions)], { type: "text/csv;charset=utf-8" }))
    const link = Object.assign(document.createElement("a"), { href: url, download: "mykhata-transactions.csv" })
    link.click()
    URL.revokeObjectURL(url)
    toast.success(`Exported ${transactions.length} transactions`)
  }

  async function deleteAll() {
    try {
      await clear()
      toast.success("All data deleted")
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not delete your data")
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your data</CardTitle>
        <CardDescription>Download or delete everything MyKhata holds</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium">Export transactions</p>
            <p className="text-sm text-muted-foreground">{transactions.length} transactions as a CSV file</p>
          </div>
          <Button variant="outline" onClick={exportCsv} disabled={!transactions.length}>
            <Download aria-hidden /> Export CSV
          </Button>
        </div>
        <div className="flex flex-col gap-3 rounded-lg border border-destructive/40 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium">Delete all data</p>
            <p className="text-sm text-muted-foreground">Removes every transaction, statement and budget. Your account stays.</p>
          </div>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" disabled={!transactions.length}>
                <Trash2 aria-hidden /> Delete all data
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete all your data?</AlertDialogTitle>
                <AlertDialogDescription>
                  {transactions.length} transactions, your statement history and all budgets will be removed. This can’t be
                  undone. Export a CSV first if you want a copy.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Keep my data</AlertDialogCancel>
                <AlertDialogAction variant="destructive" onClick={() => void deleteAll()}>
                  Delete everything
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </CardContent>
    </Card>
  )
}
