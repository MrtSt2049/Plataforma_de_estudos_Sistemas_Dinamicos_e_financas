import type { Config } from 'tailwindcss'
import { colors, fontFamily, radius } from './src/theme/tokens.ts'

// The single source of the visual values is src/theme/tokens.ts, which a test keeps
// equal to the scientific engine's theme (the charts) and checks for contrast.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors,
      fontFamily: {
        sans: [...fontFamily.sans],
        mono: [...fontFamily.mono],
        code: [...fontFamily.code],
      },
      borderRadius: { sm: radius.sm, md: radius.md, lg: radius.lg },
    },
  },
} satisfies Config
