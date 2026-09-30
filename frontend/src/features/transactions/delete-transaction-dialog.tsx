"use client"

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
} from "@/components/ui/alert-dialog"
import { ApiError } from "@/lib/api"
import { formatDate, formatINR } from "@/lib/finance/format"
import type { Transaction } from "@/lib/finance/types"

import { useTransactions } from "./transactions-provider"

export function DeleteTransactionDialog({ transaction, onOpenChange }: {
  transaction?: Transaction
  onOpenChange: (open: boolean) => void
}) {
  const { add, remove } = useTransactions()

  async function confirm() {
    if (!transaction) return
    const { date, narration, type, amount, category, note } = transaction
    try {
      await remove(transaction.id)
      toast("Transaction deleted", {
        action: {
          label: "Undo",
          onClick: () => void add({ date, narration, type, amount, category, note }).catch(() => toast.error("Could not restore it")),
        },
      })
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Could not delete the transaction")
    }
  }

  return (
    <AlertDialog open={Boolean(transaction)} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this transaction?</AlertDialogTitle>
          <AlertDialogDescription>
            {transaction && (
              <>
                {formatINR(transaction.amount)} on {formatDate(transaction.date)}. It will be removed from your totals and
                charts.
              </>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Keep it</AlertDialogCancel>
          <AlertDialogAction variant="destructive" onClick={confirm}>
            Delete transaction
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
