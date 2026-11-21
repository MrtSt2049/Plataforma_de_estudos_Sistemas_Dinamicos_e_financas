import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Badge } from './Badge'
import { Button } from './Button'
import { EmptyState } from './EmptyState'
import { ErrorState } from './ErrorState'
import { Input } from './Input'
import { Panel } from './Panel'
import { Skeleton } from './Skeleton'

describe('Button', () => {
  it('is a button that does not submit forms unless asked to', () => {
    render(<Button>Salvar</Button>)
    expect(screen.getByRole('button', { name: 'Salvar' })).toHaveAttribute('type', 'button')
  })

  it('calls onClick', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Ir</Button>)
    await userEvent.click(screen.getByRole('button', { name: 'Ir' }))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('blocks clicks and says it is busy while loading', async () => {
    const onClick = vi.fn()
    render(
      <Button loading onClick={onClick}>
        Enviando
      </Button>,
    )
    const button = screen.getByRole('button', { name: 'Enviando' })
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-busy', 'true')
    await userEvent.click(button)
    expect(onClick).not.toHaveBeenCalled()
  })

  it('can be disabled', () => {
    render(<Button disabled>Nada</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
    expect(screen.getByRole('button')).not.toHaveAttribute('aria-busy')
  })
})

describe('Input', () => {
  it('labels the field', () => {
    render(<Input label="E-mail" />)
    expect(screen.getByLabelText('E-mail')).toBeInTheDocument()
  })

  it('announces an error and marks the field invalid', () => {
    render(<Input label="Senha" error="Use pelo menos 8 caracteres." />)
    const field = screen.getByLabelText('Senha')
    expect(field).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByRole('alert')).toHaveTextContent('Use pelo menos 8 caracteres.')
    expect(field).toHaveAccessibleDescription('Use pelo menos 8 caracteres.')
  })

  it('shows a hint without raising an alert', () => {
    render(<Input label="Senha" hint="Pelo menos 8 caracteres." />)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByLabelText('Senha')).toHaveAccessibleDescription('Pelo menos 8 caracteres.')
    expect(screen.getByLabelText('Senha')).not.toHaveAttribute('aria-invalid')
  })

  it('prefers the error over the hint', () => {
    render(<Input label="Senha" hint="dica" error="erro" />)
    expect(screen.getByLabelText('Senha')).toHaveAccessibleDescription('erro')
  })

  it('keeps ids unique when there are several fields', () => {
    render(
      <>
        <Input label="A" />
        <Input label="B" />
      </>,
    )
    expect(screen.getByLabelText('A').id).not.toBe(screen.getByLabelText('B').id)
  })
})

describe('Badge', () => {
  it.each(['success', 'running', 'failed', 'queued', 'demo', 'dynamical'] as const)('renders the %s badge with its text', (variant) => {
    render(<Badge variant={variant}>{variant}</Badge>)
    expect(screen.getByText(variant)).toBeInTheDocument()
  })
})

describe('Panel', () => {
  it('renders the title, the aside and the content', () => {
    render(
      <Panel title="Estado" aside={<span>lado</span>}>
        conteúdo
      </Panel>,
    )
    expect(screen.getByRole('heading', { name: 'Estado' })).toBeInTheDocument()
    expect(screen.getByText('lado')).toBeInTheDocument()
    expect(screen.getByText('conteúdo')).toBeInTheDocument()
  })
})

describe('Skeleton', () => {
  it('announces itself as a busy status', () => {
    render(<Skeleton label="Carregando experimentos" />)
    const status = screen.getByRole('status', { name: 'Carregando experimentos' })
    expect(status).toHaveAttribute('aria-busy', 'true')
    expect(status.children).toHaveLength(3)
  })
})

describe('EmptyState', () => {
  it('explains the emptiness and offers the action that resolves it', () => {
    render(<EmptyState title="Nada aqui" description="Crie o primeiro." action={<button>Criar</button>} />)
    expect(screen.getByText('Nada aqui')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Criar' })).toBeInTheDocument()
  })

  it('works without an action', () => {
    render(<EmptyState title="Nada" description="Vazio." />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})

describe('ErrorState', () => {
  it('shows the message as an alert and retries on request', async () => {
    const onRetry = vi.fn()
    render(<ErrorState message="Falhou" onRetry={onRetry} />)
    expect(screen.getByRole('alert')).toHaveTextContent('Falhou')
    await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('offers no retry when there is nothing to retry', () => {
    render(<ErrorState message="Falhou" />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
