import { describe, expect, it } from 'vitest'
import { authErrorMessage } from './authMessages'
import { cx } from './cx'
import { safeDestination } from './safeDestination'
import { emailError, MIN_PASSWORD_LENGTH, passwordError } from './validation'

describe('cx', () => {
  it('joins the truthy parts and skips the rest', () => {
    expect(cx('a', false, null, undefined, '', 'b')).toBe('a b')
    expect(cx()).toBe('')
  })
})

describe('safeDestination', () => {
  it.each([
    ['/experimentos', '/experimentos'],
    ['/', '/'],
    ['//evil.example', '/'],
    ['https://evil.example', '/'],
    ['javascript:alert(1)', '/'],
    ['relative', '/'],
    [undefined, '/'],
    [42, '/'],
    [null, '/'],
  ])('%j becomes %s', (input, expected) => {
    expect(safeDestination(input)).toBe(expected)
  })
})

describe('validation', () => {
  it('accepts plausible e-mails and rejects the rest', () => {
    expect(emailError('a@b.co')).toBeUndefined()
    expect(emailError('  a@b.co  ')).toBeUndefined()
    for (const bad of ['', 'a', 'a@b', '@b.co', 'a b@c.de']) expect(emailError(bad)).toBeDefined()
  })

  it('requires the minimum password length', () => {
    expect(passwordError('x'.repeat(MIN_PASSWORD_LENGTH))).toBeUndefined()
    expect(passwordError('x'.repeat(MIN_PASSWORD_LENGTH - 1))).toContain(String(MIN_PASSWORD_LENGTH))
  })
})

describe('authErrorMessage', () => {
  it.each([
    ['invalid_credentials', /incorretos/],
    ['email_not_confirmed', /Confirme seu e-mail/],
    ['weak_password', /fraca/],
    ['same_password', /diferente/],
    ['signup_disabled', /desativado/],
    ['over_request_rate_limit', /Muitas tentativas/],
    ['over_email_send_rate_limit', /Muitas tentativas/],
  ])('maps %s to a specific message', (code, pattern) => {
    expect(authErrorMessage({ code })).toMatch(pattern)
  })

  it('does not echo an unknown code or message', () => {
    expect(authErrorMessage({ code: 'something_internal', status: 500 })).toBe('Não foi possível concluir a operação. Tente de novo.')
  })

  it('suggests checking the connection when there is no status', () => {
    expect(authErrorMessage({})).toMatch(/conexão/)
    expect(authErrorMessage({ status: 0 })).toMatch(/conexão/)
  })
})
