/** The server's policy has the last word; this only avoids useless round trips. */
export const MIN_PASSWORD_LENGTH = 8

const EMAIL_SHAPE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function emailError(email: string): string | undefined {
  return EMAIL_SHAPE.test(email.trim()) ? undefined : 'Informe um e-mail válido.'
}

export function passwordError(password: string): string | undefined {
  return password.length >= MIN_PASSWORD_LENGTH
    ? undefined
    : `Use pelo menos ${MIN_PASSWORD_LENGTH} caracteres.`
}
