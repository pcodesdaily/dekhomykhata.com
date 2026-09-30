"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { format } from "date-fns"
import { Sparkles } from "lucide-react"
import { useEffect, useState } from "react"
import { Controller, useForm, useWatch } from "react-hook-form"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { ApiError, api } from "@/lib/api"
import { CATEGORIES, categoriesFor } from "@/lib/finance/categories"
import type { CategoryId, Transaction } from "@/lib/finance/types"

import { transactionSchema, type TransactionInput, type TransactionValues } from "./schema"
import { useTransactions } from "./transactions-provider"

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  transaction?: Transaction
}

const emptyValues = (): TransactionInput => ({
  date: format(new Date(), "yyyy-MM-dd"),
  narration: "",
  type: "DEBIT",
  amount: "",
  category: "FOOD_DINING",
  note: "",
})

export function TransactionFormDialog({ open, onOpenChange, transaction }: Props) {
  const { add, update } = useTransactions()
  const editing = Boolean(transaction)
  const form = useForm<TransactionInput, unknown, TransactionValues>({
    resolver: zodResolver(transactionSchema),
    defaultValues: emptyValues(),
  })
  const type = useWatch({ control: form.control, name: "type" })

  const [suggesting, setSuggesting] = useState(false)

  useEffect(() => {
    if (open) form.reset(transaction ? { ...transaction, note: transaction.note ?? "" } : emptyValues())
  }, [open, transaction, form])

  async function onSubmit(values: TransactionValues) {
    const payload = { ...values, note: values.note || null }
    try {
      if (transaction) await update(transaction.id, payload)
      else await add(payload)
      toast.success(transaction ? "Transaction updated" : "Transaction added")
      onOpenChange(false)
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Could not save the transaction")
    }
  }

  async function suggest() {
    const { narration, type, amount } = form.getValues()
    if (!narration || String(narration).trim().length < 2) return form.setError("narration", { message: "Describe the transaction first" })
    setSuggesting(true)
    try {
      const result = await api<{ category: CategoryId; confidence: number }>("/categorise", {
        method: "POST",
        json: { narration, type, amount: Number(amount) > 0 ? Number(amount) : 1 },
      })
      if (categoriesFor(type).includes(result.category)) {
        form.setValue("category", result.category, { shouldValidate: true })
        toast(`Suggested ${CATEGORIES[result.category].label}`, { description: `${Math.round(result.confidence * 100)}% confident` })
      } else {
        toast("No confident suggestion for this direction")
      }
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Could not get a suggestion")
    } finally {
      setSuggesting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90dvh] overflow-y-auto overscroll-contain sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{editing ? "Edit transaction" : "Add transaction"}</DialogTitle>
          <DialogDescription>
            {editing ? "Change the details or fix the category." : "Record cash spends or anything missing from your statement."}
          </DialogDescription>
        </DialogHeader>
        <form id="transaction-form" onSubmit={form.handleSubmit(onSubmit)} noValidate>
          <FieldGroup>
            <Controller
              name="type"
              control={form.control}
              render={({ field }) => (
                <Field>
                  <FieldLabel>Direction</FieldLabel>
                  <ToggleGroup
                    type="single"
                    variant="outline"
                    value={field.value}
                    onValueChange={(value) => {
                      if (!value) return
                      field.onChange(value)
                      const current = form.getValues("category")
                      if (!categoriesFor(value as Transaction["type"]).includes(current)) {
                        form.setValue("category", value === "CREDIT" ? "SALARY" : "FOOD_DINING")
                      }
                    }}
                    className="w-full"
                  >
                    <ToggleGroupItem value="DEBIT" className="flex-1">Money out</ToggleGroupItem>
                    <ToggleGroupItem value="CREDIT" className="flex-1">Money in</ToggleGroupItem>
                  </ToggleGroup>
                </Field>
              )}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <Controller
                name="amount"
                control={form.control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="tx-amount">Amount (₹)</FieldLabel>
                    <Input
                      {...field}
                      value={field.value as string | number}
                      id="tx-amount"
                      inputMode="decimal"
                      placeholder="0"
                      autoComplete="off"
                      aria-invalid={fieldState.invalid}
                    />
                    <FieldError errors={[fieldState.error]} />
                  </Field>
                )}
              />
              <Controller
                name="date"
                control={form.control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="tx-date">Date</FieldLabel>
                    <Input {...field} id="tx-date" type="date" autoComplete="off" aria-invalid={fieldState.invalid} />
                    <FieldError errors={[fieldState.error]} />
                  </Field>
                )}
              />
            </div>
            <Controller
              name="narration"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="tx-narration">Description</FieldLabel>
                  <Input
                    {...field}
                    id="tx-narration"
                    placeholder="e.g. Groceries at D-Mart…"
                    autoComplete="off"
                    aria-invalid={fieldState.invalid}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />
            <Controller
              name="category"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <div className="flex items-center justify-between">
                    <FieldLabel htmlFor="tx-category">Category</FieldLabel>
                    <Button type="button" variant="ghost" size="sm" className="h-7" onClick={suggest} disabled={suggesting}>
                      <Sparkles aria-hidden /> {suggesting ? "Suggesting…" : "Suggest"}
                    </Button>
                  </div>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="tx-category" aria-invalid={fieldState.invalid} className="w-full">
                      <SelectValue placeholder="Choose a category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categoriesFor(type).map((id) => (
                        <SelectItem key={id} value={id}>
                          {CATEGORIES[id].label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />
            <Controller
              name="note"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="tx-note">Note (optional)</FieldLabel>
                  <Textarea {...field} id="tx-note" rows={2} autoComplete="off" aria-invalid={fieldState.invalid} />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />
          </FieldGroup>
        </form>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button type="submit" form="transaction-form" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? "Saving…" : editing ? "Save changes" : "Add transaction"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
