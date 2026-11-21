import { useState } from 'react'

export interface ChartDataPoint {
  x: number | string
  y: number
  label?: string
}

export interface ScientificChartProps {
  title: string
  subtitle?: string
  data: ChartDataPoint[]
  color?: string
  type?: 'line' | 'area' | 'bar'
  unit?: string
  height?: number
  baselineZero?: boolean
  className?: string
}

/**
 * Lightweight, high-performance scientific chart component conforming strictly
 * to the QuantLab design system:
 * - `#0B0F14` canvas / `#111820` panel background
 * - 1px hairline grid in `#263442`
 * - 2px stroke width with tabular mono typography
 * - Responsive SVG vector scaling
 */
export function ScientificChart({
  title,
  subtitle,
  data,
  color = '#3B82F6', // analytic blue
  type = 'line',
  unit = '',
  height = 240,
  baselineZero = false,
  className = '',
}: ScientificChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<ChartDataPoint | null>(null)

  if (!data || data.length === 0) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center rounded-md border border-line bg-panel text-xs text-fg-muted"
      >
        Sem dados para exibir
      </div>
    )
  }

  const padding = { top: 20, right: 20, bottom: 30, left: 55 }
  const viewBoxWidth = 600
  const viewBoxHeight = height

  const innerWidth = viewBoxWidth - padding.left - padding.right
  const innerHeight = viewBoxHeight - padding.top - padding.bottom

  const yValues = data.map((d) => d.y)
  const minYRaw = Math.min(...yValues)
  const maxYRaw = Math.max(...yValues)

  const minY = baselineZero ? Math.min(0, minYRaw) : minYRaw - (maxYRaw - minYRaw) * 0.05
  const maxY = baselineZero ? Math.max(0, maxYRaw) : maxYRaw + (maxYRaw - minYRaw) * 0.05
  const yRange = maxY - minY || 1

  const getX = (index: number) => padding.left + (index / (data.length - 1 || 1)) * innerWidth
  const getY = (val: number) => padding.top + innerHeight - ((val - minY) / yRange) * innerHeight

  const pointsPath = data
    .map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(d.y)}`)
    .join(' ')

  const areaPath = `${pointsPath} L ${getX(data.length - 1)} ${padding.top + innerHeight} L ${getX(0)} ${
    padding.top + innerHeight
  } Z`

  // Grid lines (4 intervals)
  const gridTicks = [0, 0.33, 0.66, 1.0].map((ratio) => {
    const val = minY + ratio * yRange
    const yPos = getY(val)
    return { val, yPos }
  })

  return (
    <div className={`flex flex-col rounded-md border border-line bg-panel p-4 ${className}`}>
      <div className="mb-2 flex items-start justify-between">
        <div>
          <h4 className="text-xs font-medium text-fg">{title}</h4>
          {subtitle && <p className="text-[11px] text-fg-muted">{subtitle}</p>}
        </div>
        {hoveredPoint && (
          <div className="flex items-center gap-2 font-mono text-xs tabular-nums text-fg">
            <span className="text-fg-muted">{hoveredPoint.label || hoveredPoint.x}:</span>
            <span className="font-semibold" style={{ color }}>
              {hoveredPoint.y.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} {unit}
            </span>
          </div>
        )}
      </div>

      <div className="relative w-full">
        <svg
          viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
          className="w-full overflow-visible select-none"
          style={{ height }}
        >
          {/* Grid lines */}
          {gridTicks.map(({ val, yPos }, idx) => (
            <g key={idx}>
              <line
                x1={padding.left}
                y1={yPos}
                x2={viewBoxWidth - padding.right}
                y2={yPos}
                stroke="#263442"
                strokeWidth="1"
              />
              <text
                x={padding.left - 8}
                y={yPos + 3}
                fill="#8997A5"
                fontSize="10"
                fontFamily="IBM Plex Mono, monospace"
                textAnchor="end"
              >
                {val.toFixed(1)}
              </text>
            </g>
          ))}

          {/* Area fill */}
          {type === 'area' && <path d={areaPath} fill={color} fillOpacity="0.12" />}

          {/* Line stroke */}
          <path d={pointsPath} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" />

          {/* Interactive hover points */}
          {data.map((d, i) => (
            <circle
              key={i}
              cx={getX(i)}
              cy={getY(d.y)}
              r="4"
              className="cursor-pointer opacity-0 hover:opacity-100 transition-opacity"
              fill={color}
              stroke="#0B0F14"
              strokeWidth="2"
              onMouseEnter={() => setHoveredPoint(d)}
              onMouseLeave={() => setHoveredPoint(null)}
            />
          ))}

          {/* X-axis labels (first, middle, last) */}
          {data.length > 1 && (
            <>
              <text
                x={getX(0)}
                y={viewBoxHeight - 6}
                fill="#8997A5"
                fontSize="10"
                fontFamily="IBM Plex Mono, monospace"
                textAnchor="start"
              >
                {String(data[0]?.label || data[0]?.x)}
              </text>
              <text
                x={getX(Math.floor(data.length / 2))}
                y={viewBoxHeight - 6}
                fill="#8997A5"
                fontSize="10"
                fontFamily="IBM Plex Mono, monospace"
                textAnchor="middle"
              >
                {String(data[Math.floor(data.length / 2)]?.label || data[Math.floor(data.length / 2)]?.x)}
              </text>
              <text
                x={getX(data.length - 1)}
                y={viewBoxHeight - 6}
                fill="#8997A5"
                fontSize="10"
                fontFamily="IBM Plex Mono, monospace"
                textAnchor="end"
              >
                {String(data[data.length - 1]?.label || data[data.length - 1]?.x)}
              </text>
            </>
          )}
        </svg>
      </div>
    </div>
  )
}
