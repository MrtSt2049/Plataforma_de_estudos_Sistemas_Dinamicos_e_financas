import type { ReactNode } from 'react'

export interface TableColumn<T> {
  header: string
  accessor: (item: T) => ReactNode
  align?: 'left' | 'center' | 'right'
  className?: string
}

export interface TableProps<T> {
  columns: readonly TableColumn<T>[]
  data: readonly T[]
  keyExtractor: (item: T) => string
  emptyMessage?: string
  className?: string
}

/**
 * Institutional dense table conforming to the QuantLab 34px row height design standard.
 */
export function Table<T>({
  columns,
  data,
  keyExtractor,
  emptyMessage = 'Nenhum dado encontrado.',
  className = '',
}: TableProps<T>) {
  if (data.length === 0) {
    return (
      <div className="py-8 text-center text-xs text-fg-muted border border-line rounded-md bg-panel">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className={`overflow-x-auto rounded-md border border-line bg-panel ${className}`}>
      <table className="w-full text-left text-xs border-collapse">
        <thead>
          <tr className="border-b border-line bg-surface/75 text-fg-muted h-[34px]">
            {columns.map((col, idx) => (
              <th
                key={idx}
                className={`px-3 py-2 font-medium ${
                  col.align === 'right'
                    ? 'text-right'
                    : col.align === 'center'
                      ? 'text-center'
                      : 'text-left'
                } ${col.className ?? ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line/50">
          {data.map((item) => (
            <tr
              key={keyExtractor(item)}
              className="h-[34px] hover:bg-surface/40 transition-colors"
            >
              {columns.map((col, idx) => (
                <td
                  key={idx}
                  className={`px-3 py-1.5 ${
                    col.align === 'right'
                      ? 'text-right font-mono tabular-nums'
                      : col.align === 'center'
                        ? 'text-center'
                        : 'text-left'
                  } ${col.className ?? ''}`}
                >
                  {col.accessor(item)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
