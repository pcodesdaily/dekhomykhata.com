import { z } from "zod"

import { CATEGORIES, CATEGORY_IDS } from "@/lib/finance/categories"
import type { CategoryId } from "@/lib/finance/types"

export const transactionSchema = z
  .object({
    date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Pick a date"),
    narration: z.string().trim().min(2, "Describe the transaction").max(200, "Keep it under 200 characters"),
    type: z.enum(["DEBIT", "CREDIT"]),
    amount: z.preprocess(
      (v) => (v === "" || v === null || v === undefined ? undefined : Number(v)),
      z
        .number({ required_error: "Enter an amount", invalid_type_error: "Enter a number" })
        .positive("Amount must be more than ₹0")
        .max(1_00_00_00_000, "Amount is too large"),
    ),
    category: z.enum(CATEGORY_IDS as [CategoryId, ...CategoryId[]]),
    note: z.string().trim().max(300, "Keep notes under 300 characters").optional(),
  })
  .refine((v) => {
    const direction = CATEGORIES[v.category].direction
    return direction === "BOTH" || direction === v.type
  }, { path: ["category"], message: "This category doesn't match money in / money out" })

export type TransactionInput = z.input<typeof transactionSchema>
export type TransactionValues = z.output<typeof transactionSchema>
