import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/services/apiClient'
import { AsyncBoundary, type AsyncQuery } from './AsyncBoundary'

function query<T>(overrides: Partial<AsyncQuery<T>>): AsyncQuery<T> {
  return { status: 'success', data: undefined, error: null, refetch: vi.fn(), ...overrides }
}

describe('AsyncBoundary: the four states of RULE 034', () => {
  it('shows a loading placeholder while pending', () => {
    render(
      <AsyncBoundary query={query<string[]>({ status: 'pending' })} empty="vazio">
        {() => 'dados'}
      </AsyncBoundary>,
    )
    expect(screen.getByRole('status')).toHaveAttribute('aria-busy', 'true')
    expect(screen.queryByText('dados')).not.toBeInTheDocument()
  })

  it('shows the error with the API message and retries', async () => {
    const refetch = vi.fn()
    render(
      <AsyncBoundary
        query={query<string[]>({ status: 'error', error: new ApiError('Símbolo não encontrado.', 404, 'symbol_not_found'), refetch })}
        empty="vazio"
      >
        {() => 'dados'}
      </AsyncBoundary>,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Símbolo não encontrado.')
    await userEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('does not leak the text of an unknown error', () => {
    render(
      <AsyncBoundary query={query<string[]>({ status: 'error', error: new Error('SELECT * FROM secrets') })} empty="vazio">
        {() => 'dados'}
      </AsyncBoundary>,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Não foi possível carregar os dados.')
    expect(screen.queryByText(/secrets/)).not.toBeInTheDocument()
  })

  it('shows the empty state when the request worked but there is nothing', () => {
    render(
      <AsyncBoundary query={query<string[]>({ data: [] })} isEmpty={(items) => items.length === 0} empty="vazio">
        {() => 'dados'}
      </AsyncBoundary>,
    )
    expect(screen.getByText('vazio')).toBeInTheDocument()
    expect(screen.queryByText('dados')).not.toBeInTheDocument()
  })

  it('renders the data on success', () => {
    render(
      <AsyncBoundary query={query<string[]>({ data: ['a', 'b'] })} isEmpty={(items) => items.length === 0} empty="vazio">
        {(items) => items.join(',')}
      </AsyncBoundary>,
    )
    expect(screen.getByText('a,b')).toBeInTheDocument()
  })

  it('treats a successful result as non-empty when no emptiness rule is given', () => {
    render(
      <AsyncBoundary query={query<number>({ data: 0 })} empty="vazio">
        {(value) => `valor ${value}`}
      </AsyncBoundary>,
    )
    expect(screen.getByText('valor 0')).toBeInTheDocument()
  })

  it('lets the caller replace the generic error for errors it understands', () => {
    render(
      <AsyncBoundary
        query={query<string[]>({ status: 'error', error: new ApiError('x', 0, 'api_not_configured') })}
        empty="vazio"
        errorOverride={(error) => (error instanceof ApiError && error.code === 'api_not_configured' ? <p>configure a API</p> : null)}
      >
        {() => 'dados'}
      </AsyncBoundary>,
    )
    expect(screen.getByText('configure a API')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('falls back to the generic error when the override declines', () => {
    render(
      <AsyncBoundary query={query<string[]>({ status: 'error', error: new Error('x') })} empty="vazio" errorOverride={() => null}>
        {() => 'dados'}
      </AsyncBoundary>,
    )
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})
