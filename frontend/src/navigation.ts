import {
  Activity,
  Database,
  FlaskConical,
  FolderOpen,
  Grid3X3,
  LayoutDashboard,
  TrendingUp,
  Waypoints,
  type LucideIcon,
} from 'lucide-react'

export interface NavItem {
  label: string
  to: string
  icon: LucideIcon
  /** False while the screen does not exist yet: the item is shown as "em breve". */
  ready: boolean
}

export interface NavGroup {
  label: string
  items: readonly NavItem[]
}

/**
 * Only what the 0.1 engine can deliver appears here (plan, section 8.7). Portfolio
 * optimization, backtesting and the like wait for new engine modules.
 */
export const navigation: readonly NavGroup[] = [
  {
    label: 'Workspace',
    items: [{ label: 'Visão geral', to: '/', icon: LayoutDashboard, ready: true }],
  },
  {
    label: 'Mercados',
    items: [{ label: 'Dados de mercado', to: '/mercados', icon: Database, ready: false }],
  },
  {
    label: 'Finanças quantitativas',
    items: [
      { label: 'Retornos', to: '/retornos', icon: TrendingUp, ready: true },
      { label: 'Risco', to: '/risco', icon: Activity, ready: true },
      { label: 'Correlação', to: '/correlacao', icon: Grid3X3, ready: false },
    ],
  },
  {
    label: 'Sistemas dinâmicos',
    items: [
      { label: 'Mapa logístico', to: '/dinamica/logistico', icon: Waypoints, ready: true },
      { label: 'Sistema de Lorenz', to: '/dinamica/lorenz', icon: Waypoints, ready: true },
    ],
  },
  {
    label: 'Pesquisa',
    items: [
      { label: 'Projetos', to: '/projetos', icon: FolderOpen, ready: true },
      { label: 'Experimentos', to: '/experimentos', icon: FlaskConical, ready: true },
    ],
  },
]
