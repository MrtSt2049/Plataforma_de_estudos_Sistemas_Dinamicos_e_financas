/**
 * QuantLab visual tokens, from the interface design system (`Assets/`).
 *
 * Colour roles (design principles):
 * - `pos` / `neg`: signed change only, and always with a sign (▲ ▼ + −), never alone;
 * - `analytic`: actions and analysis; `science`: dynamical systems;
 * - `warn`: alerts and the DEMO badge.
 *
 * The raw `neg`, `analytic` and `science` fail the 4.5:1 text contrast on the panel
 * surfaces, so they are for fills and lines. Text uses the `*-text` variants. A test
 * checks the contrast, and another one keeps these values equal to the engine's chart
 * theme (`engine/quantlab/visualization/theme.py`).
 */
export const colors = {
  canvas: '#0B0F14',
  panel: '#111820',
  surface: '#17212B',
  line: '#263442',
  fg: '#E8EDF2',
  'fg-muted': '#8997A5',
  pos: '#16C784',
  neg: '#EA3943',
  analytic: '#3B82F6',
  action: '#2563EB',
  science: '#8B5CF6',
  warn: '#F5A623',
  // Lighter variants for text. `neg-text` and `analytic-text` come from the design;
  // `science-text` is derived here and validated by the contrast test.
  'neg-text': '#F0525B',
  'analytic-text': '#6EA3FF',
  'science-text': '#A78BFA',
} as const

export type ColorToken = keyof typeof colors

/** Colours that carry text, with the surfaces they may sit on. */
export const textTokens = [
  'fg',
  'fg-muted',
  'pos',
  'warn',
  'neg-text',
  'analytic-text',
  'science-text',
] as const satisfies readonly ColorToken[]

export const surfaceTokens = ['canvas', 'panel', 'surface'] as const satisfies readonly ColorToken[]

export const fontFamily = {
  sans: ['Inter Variable', 'Inter', 'system-ui', 'sans-serif'],
  mono: ['IBM Plex Mono', 'JetBrains Mono', 'monospace'],
  code: ['JetBrains Mono', 'IBM Plex Mono', 'monospace'],
} as const

export const radius = { sm: '3px', md: '5px', lg: '6px' } as const

/** 4 px spacing grid and the dense table row of the design. */
export const layout = { grid: 4, rowHeight: 34 } as const
