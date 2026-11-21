/// <reference types="node" />
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { colors, surfaceTokens, textTokens, type ColorToken } from './tokens'

// The engine's chart theme is the source of truth for the values (plan F1).
// Tests run from frontend/ (npm test), where the engine is one level up.
const engineTheme = readFileSync(resolve(process.cwd(), '../engine/quantlab/visualization/theme.py'), 'utf-8')

function engineColor(name: string): string {
  const match = new RegExp(`^${name}: Final = "(#[0-9A-Fa-f]{6})"`, 'm').exec(engineTheme)
  if (match?.[1] === undefined) throw new Error(`${name} not found in theme.py`)
  return match[1].toUpperCase()
}

function luminance(hex: string): number {
  const channels = [1, 3, 5].map((start) => parseInt(hex.slice(start, start + 2), 16) / 255)
  const [r = 0, g = 0, b = 0] = channels.map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function contrast(foreground: string, background: string): number {
  const [light, dark] = [luminance(foreground), luminance(background)].sort((a, b) => b - a)
  return ((light ?? 0) + 0.05) / ((dark ?? 0) + 0.05)
}

describe('tokens', () => {
  it.each<[ColorToken, string]>([
    ['canvas', 'BACKGROUND'],
    ['panel', 'PANEL'],
    ['surface', 'SURFACE'],
    ['line', 'BORDER'],
    ['fg', 'TEXT'],
    ['fg-muted', 'TEXT_SECONDARY'],
    ['pos', 'POSITIVE'],
    ['neg', 'NEGATIVE'],
    ['analytic', 'ANALYTIC'],
    ['science', 'SCIENCE'],
    ['warn', 'WARN'],
  ])('%s equals the engine chart theme (%s)', (token, engineName) => {
    expect(colors[token].toUpperCase()).toBe(engineColor(engineName))
  })

  it.each(surfaceTokens.flatMap((surface) => textTokens.map((text) => [text, surface] as const)))(
    'text token %s is readable on %s (WCAG AA, 4.5:1)',
    (text, surface) => {
      expect(contrast(colors[text], colors[surface])).toBeGreaterThanOrEqual(4.5)
    },
  )

  it('white text on the action colour is readable', () => {
    expect(contrast('#FFFFFF', colors.action)).toBeGreaterThanOrEqual(4.5)
  })

  it('explains why the text variants exist: the raw colours fail on some surface', () => {
    const rawFailures = (['neg', 'analytic', 'science'] as const).filter((token) =>
      surfaceTokens.some((surface) => contrast(colors[token], colors[surface]) < 4.5),
    )
    expect(rawFailures).toEqual(['neg', 'analytic', 'science'])
  })
})
