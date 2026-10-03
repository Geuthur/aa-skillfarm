// React
import { useLocation } from "react-router-dom";

// Third Party
import {
  flexRender,
  getCoreRowModel,
  getFacetedMinMaxValues,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import type {
  Cell,
  ColumnDef,
  InitialTableState,
  Row,
} from "@tanstack/react-table";
import {
  ArrowUpDown,
  ChevronDown,
  ChevronFirst,
  ChevronLast,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
} from "lucide-react";
import { Button, Form, Table } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "./BaseTable.module.css";

import BaseHeader from "@/Components/Tables/BaseTable/BaseTableHeader";
import BasePages from "@/Components/Tables/BaseTable/BaseTablePages";

const isNumber = <TData,>(cell: Cell<TData, unknown>) => typeof cell.getValue() === "number";

export interface BaseTableProps<TData, TValue = unknown> {
  isFetching?: boolean;
  isError?: boolean;
  debugTable?: boolean;
  striped?: boolean;
  hover?: boolean;
  data?: TData[];
  columns: ColumnDef<TData, TValue>[];
  initialState?: InitialTableState;
  exportFileName?: string;
  variant?: "bootstrap" | "vowra";
  emptyText?: string;
  className?: string;
  tableClassName?: string;
  pageSizeOptions?: number[];
  itemLabel?: string;
  getRowClassName?: (row: Row<TData>) => string;
}

const BaseTable = <TData, TValue = unknown>({
  isFetching = false,
  isError = false,
  debugTable = false,
  data = [],
  columns,
  striped = false,
  hover = false,
  initialState = undefined,
  exportFileName = undefined,
  variant = "vowra",
  emptyText,
  className,
  tableClassName,
  pageSizeOptions = [10, 25, 50, 100],
  itemLabel,
  getRowClassName,
}: BaseTableProps<TData, TValue>) => {
  const location = useLocation();
  const { t } = useTranslation();

  // TanStack Table's useReactTable() returns functions the compiler can't
  // safely memoize; this is inherent to the library, not fixable here.

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
    getFacetedMinMaxValues: getFacetedMinMaxValues(),
    debugTable,
    initialState: {
      pagination: { pageSize: 15 },
      ...initialState,
    },
  });

  const { rows } = table.getRowModel();
  const fileName =
    exportFileName !== undefined ? exportFileName : `ExportedData_${location.pathname}`;

  if (variant === "vowra") {
    const totalCount = table.getPrePaginationRowModel().rows.length;
    const pageIndex = table.getState().pagination.pageIndex;
    const pageSize = table.getState().pagination.pageSize;
    const pageCount = table.getPageCount();

    return (
      <div
        className={`mt-2 rounded-xl shadow-lg overflow-hidden border border-zinc-700/80 bg-zinc-900/60 backdrop-blur-md ${className ?? ""}`}
      >
        <div className="overflow-x-auto">
          <table
            className={`w-full text-left text-xs font-mono-tech ${tableClassName ?? ""}`}
          >
            <thead
              className="bg-[#0b0e14] border-b border-zinc-700/80 text-zinc-400 uppercase text-[11px] font-hud tracking-wider"
            >
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    const canSort = header.column.getCanSort();
                    const isSorted = header.column.getIsSorted();
                    return (
                      <th
                        key={header.id}
                        colSpan={header.colSpan}
                        onClick={canSort ? header.column.getToggleSortingHandler() : undefined}
                        className={`py-3 px-4 ${
                          canSort
                            ? "cursor-pointer select-none group transition-colors hover:text-emerald-400"
                            : ""
                        }`}
                      >
                        <div className="flex items-center gap-1.5">
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {canSort && (
                            <span>
                              {isSorted === "asc" ? (
                                <ChevronUp className="w-3.5 h-3.5 text-emerald-400" />
                              ) : isSorted === "desc" ? (
                                <ChevronDown className="w-3.5 h-3.5 text-emerald-400" />
                              ) : (
                                <ArrowUpDown className="w-3 h-3 transition-colors text-zinc-600 group-hover:text-zinc-400" />
                              )}
                            </span>
                          )}
                        </div>
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-zinc-800/80">
              {isError ? (
                <tr>
                  <td
                    colSpan={table.getVisibleLeafColumns().length}
                    className="py-10 text-center text-zinc-400 font-mono-tech"
                  >
                    {t("Something went wrong.")}
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={table.getVisibleLeafColumns().length}
                    className="py-10 text-center text-zinc-400 font-mono-tech"
                  >
                    {emptyText ?? t("No Data Available")}
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr
                    key={row.id}
                    className={`transition-colors ${
                      getRowClassName
                        ? getRowClassName(row)
                        : "hover:bg-zinc-800/50"
                    }`}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td
                        key={cell.id}
                        className={`py-3 px-4 text-zinc-300 ${styles["cell"]}`}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* DataTable Footer Controls */}
        <div
          className="flex flex-col sm:flex-row items-center justify-between p-3.5 border-t border-zinc-700/80 font-mono-tech text-xs text-zinc-400 gap-3 bg-[#0b0e14]/90"
        >
          {/* Page Size Selector & Count Indicator */}
          <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-start">
            <div className="flex items-center gap-2">
              <span>{t("Page Size:")}</span>
              <Form.Select
                size="sm"
                value={pageSize}
                onChange={(e) => table.setPageSize(Number(e.target.value))}
                className={`bg-zinc-900 border border-zinc-700 text-zinc-200 text-xs font-mono-tech py-1 px-2 rounded focus:outline-none focus:border-emerald-500 cursor-pointer ${styles["page-size-select"]}`}
              >
                {pageSizeOptions.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
                <option value={1000000}>{t("Show All")}</option>
              </Form.Select>
            </div>

            {totalCount > 0 && (
              <span className="text-[11px] text-zinc-400">
                {pageSize >= 1000000
                  ? t("Showing all {{total}} {{items}}", {
                      total: totalCount,
                      items: itemLabel ?? t("entries"),
                    })
                  : t("Showing {{start}}-{{end}} of {{total}} {{items}}", {
                      start: pageIndex * pageSize + 1,
                      end: Math.min((pageIndex + 1) * pageSize, totalCount),
                      total: totalCount,
                      items: itemLabel ?? t("entries"),
                    })}
              </span>
            )}
          </div>

          {/* Pagination Buttons */}
          {pageCount > 1 && (
            <div className="flex items-center gap-1.5">
              <Button
                size="sm"
                disabled={!table.getCanPreviousPage()}
                onClick={() => table.setPageIndex(0)}
                className="p-1.5 text-xs rounded bg-zinc-900 border border-zinc-700 hover:bg-zinc-800 text-zinc-300 disabled:opacity-40 cursor-pointer transition-colors"
                title={t("First Page")}
              >
                <ChevronFirst className="w-3.5 h-3.5" />
              </Button>
              <Button
                size="sm"
                disabled={!table.getCanPreviousPage()}
                onClick={() => table.previousPage()}
                className="p-1.5 text-xs rounded bg-zinc-900 border border-zinc-700 hover:bg-zinc-800 text-zinc-300 disabled:opacity-40 cursor-pointer transition-colors"
                title={t("Previous Page")}
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </Button>

              <span className="px-2 font-semibold text-[11px] text-zinc-300">
                {t("Page {{page}} of {{total}}", {
                  page: pageIndex + 1,
                  total: pageCount,
                })}
              </span>

              <Button
                size="sm"
                disabled={!table.getCanNextPage()}
                onClick={() => table.nextPage()}
                className="p-1.5 text-xs rounded bg-zinc-900 border border-zinc-700 hover:bg-zinc-800 text-zinc-300 disabled:opacity-40 cursor-pointer transition-colors"
                title={t("Next Page")}
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </Button>
              <Button
                size="sm"
                disabled={!table.getCanNextPage()}
                onClick={() => table.setPageIndex(pageCount - 1)}
                className="p-1.5 text-xs rounded bg-zinc-900 border border-zinc-700 hover:bg-zinc-800 text-zinc-300 disabled:opacity-40 cursor-pointer transition-colors"
                title={t("Last Page")}
              >
                <ChevronLast className="w-3.5 h-3.5" />
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <>
      <Table {...{ striped, hover }}>
        <thead>
          <BaseHeader table={table} />
        </thead>
        <tbody>
          {isError ? (
            <tr>
              <td className="text-center" colSpan={table.getVisibleLeafColumns().length}>
                {t("No Data Available")}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className={`${styles["cell"]} ${isNumber(cell) ? styles["cell-right"] : styles["cell-left"]}`}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </Table>
      <BasePages table={table} isFetching={isFetching} fileName={fileName} />
      {debugTable && (
        <div className="col-xs-12">
          <div>{t("{{count}} Rows", { count: table.getRowModel().rows.length })}</div>
          <pre>{JSON.stringify(table.getState(), null, 2)}</pre>
        </div>
      )}
    </>
  );
};

export default BaseTable;
