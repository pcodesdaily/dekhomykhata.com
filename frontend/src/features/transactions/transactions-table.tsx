"use client"

import {
  columnFilteringFeature,
  createColumnHelper,
  createFilteredRowModel,
  createPaginatedRowModel,
  createSortedRowModel,
  filterFn_equalsString,
  filterFn_includesString,
  rowPaginationFeature,
  rowSortingFeature,
  sortFn_alphanumeric,
  sortFn_basic,
  tableFeatures,
  useTable,
  type Column,
} from "@tanstack/react-table"
import { ArrowDownUp, ArrowDown, ArrowUp, MoreHorizontal, Pencil, Plus, Search, Trash2 } from "lucide-react"
import { useMemo, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { CATEGORIES, CATEGORY_IDS } from "@/lib/finance/categories"
import { formatDate, formatINR } from "@/lib/finance/format"
import type { Transaction } from "@/lib/finance/types"
import { cn } from "@/lib/utils"

import { DeleteTransactionDialog } from "./delete-transaction-dialog"
import { TransactionFormDialog } from "./transaction-form-dialog"
import { useTransactions } from "./transactions-provider"

const features = tableFeatures({
  rowSortingFeature,
  sortedRowModel: createSortedRowModel(),
  sortFns: { basic: sortFn_basic, alphanumeric: sortFn_alphanumeric },
  columnFilteringFeature,
  filteredRowModel: createFilteredRowModel(),
  filterFns: { includesString: filterFn_includesString, equalsString: filterFn_equalsString },
  rowPaginationFeature,
  paginatedRowModel: createPaginatedRowModel(),
})

const helper = createColumnHelper<typeof features, Transaction>()
const ALL = "ALL"

function SortHeader<TValue>({ column, label, align = "left" }: {
  column: Column<typeof features, Transaction, TValue>
  label: string
  align?: "left" | "right"
}) {
  const sorted = column.getIsSorted()
  const Icon = sorted === "asc" ? ArrowUp : sorted === "desc" ? ArrowDown : ArrowDownUp
  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn("-mx-2 h-8", align === "right" && "ml-auto flex")}
      onClick={() => column.toggleSorting(sorted === "asc")}
    >
      {label}
      <Icon className="size-3.5 text-muted-foreground" aria-hidden />
    </Button>
  )
}

export function TransactionsTable({ pageSize = 8 }: { pageSize?: number }) {
  const { transactions } = useTransactions()
  const [editing, setEditing] = useState<Transaction | undefined>()
  const [formOpen, setFormOpen] = useState(false)
  const [deleting, setDeleting] = useState<Transaction | undefined>()

  const columns = useMemo(
    () =>
      helper.columns([
        helper.accessor("date", {
          header: ({ column }) => <SortHeader column={column} label="Date" />,
          sortFn: "alphanumeric",
          cell: ({ getValue }) => <span className="whitespace-nowrap tabular-nums">{formatDate(getValue())}</span>,
        }),
        helper.accessor("narration", {
          header: "Description",
          filterFn: "includesString",
          cell: ({ row }) => (
            <div className="flex min-w-0 flex-col gap-0.5">
              <span className="max-w-[28ch] truncate font-mono text-xs sm:max-w-[40ch]" title={row.original.narration}>
                {row.original.narration}
              </span>
              {row.original.source === "manual" && <span className="text-xs text-muted-foreground">Added by you</span>}
            </div>
          ),
        }),
        helper.accessor("category", {
          header: "Category",
          filterFn: "equalsString",
          cell: ({ row }) => {
            const { category, confidence } = row.original
            const unsure = category === "OTHER"
            return (
              <Badge variant={unsure ? "outline" : "secondary"} title={confidence ? `Model confidence ${Math.round(confidence * 100)}%` : undefined}>
                {CATEGORIES[category].label}
              </Badge>
            )
          },
        }),
        helper.accessor("amount", {
          header: ({ column }) => <SortHeader column={column} label="Amount" align="right" />,
          sortFn: "basic",
          cell: ({ row }) => {
            const credit = row.original.type === "CREDIT"
            return (
              <div className={cn("text-right font-medium tabular-nums", credit && "text-emerald-700 dark:text-emerald-400")}>
                <span className="sr-only">{credit ? "Money in" : "Money out"} </span>
                {credit ? "+" : "−"}
                {formatINR(row.original.amount)}
              </div>
            )
          },
        }),
        helper.display({
          id: "actions",
          header: () => <span className="sr-only">Actions</span>,
          cell: ({ row }) => (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="size-8" aria-label={`Actions for ${row.original.narration}`}>
                  <MoreHorizontal className="size-4" aria-hidden />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onSelect={() => {
                    setEditing(row.original)
                    setFormOpen(true)
                  }}
                >
                  <Pencil aria-hidden /> Edit
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive" onSelect={() => setDeleting(row.original)}>
                  <Trash2 aria-hidden /> Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ),
        }),
      ]),
    [],
  )

  const table = useTable({
    features,
    columns,
    data: transactions,
    getRowId: (row) => row.id,
    initialState: { pagination: { pageIndex: 0, pageSize }, sorting: [{ id: "date", desc: true }] },
  })

  const search = (table.getColumn("narration")?.getFilterValue() as string) ?? ""
  const category = (table.getColumn("category")?.getFilterValue() as string) ?? ALL
  const rows = table.getRowModel().rows
  const filteredCount = table.getFilteredRowModel().rows.length
  const { pageIndex } = table.state.pagination

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input
            type="search"
            name="search"
            aria-label="Search transactions"
            placeholder="Search description…"
            value={search}
            onChange={(e) => table.getColumn("narration")?.setFilterValue(e.target.value)}
            className="pl-8"
            autoComplete="off"
          />
        </div>
        <Select
          value={category}
          onValueChange={(value) => table.getColumn("category")?.setFilterValue(value === ALL ? undefined : value)}
        >
          <SelectTrigger className="w-full sm:w-52" aria-label="Filter by category">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All categories</SelectItem>
            {CATEGORY_IDS.map((id) => (
              <SelectItem key={id} value={id}>
                {CATEGORIES[id].label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          onClick={() => {
            setEditing(undefined)
            setFormOpen(true)
          }}
        >
          <Plus aria-hidden /> Add transaction
        </Button>
      </div>

      <div className="overflow-hidden rounded-lg border">
        <Table>
          <TableHeader className="bg-muted/50">
            {table.getHeaderGroups().map((group) => (
              <TableRow key={group.id}>
                {group.headers.map((header) => (
                  <TableHead key={header.id} className={header.column.id === "amount" ? "text-right" : undefined}>
                    {header.isPlaceholder ? null : <table.FlexRender header={header} />}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {rows.length ? (
              rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getAllCells().map((cell) => (
                    <TableCell key={cell.id} className={cell.column.id === "actions" ? "w-10" : undefined}>
                      <table.FlexRender cell={cell} />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length}>
                  <Empty className="py-8">
                    <EmptyHeader>
                      <EmptyTitle>No transactions found</EmptyTitle>
                      <EmptyDescription>Try another search or category, or add a transaction.</EmptyDescription>
                    </EmptyHeader>
                  </Empty>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between gap-2 text-sm text-muted-foreground">
        <span aria-live="polite">
          {filteredCount} transaction{filteredCount === 1 ? "" : "s"}
          {filteredCount > 0 && ` · page ${pageIndex + 1} of ${table.getPageCount()}`}
        </span>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
            Previous
          </Button>
          <Button variant="outline" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
            Next
          </Button>
        </div>
      </div>

      <TransactionFormDialog open={formOpen} onOpenChange={setFormOpen} transaction={editing} />
      <DeleteTransactionDialog transaction={deleting} onOpenChange={(open) => !open && setDeleting(undefined)} />
    </div>
  )
}
