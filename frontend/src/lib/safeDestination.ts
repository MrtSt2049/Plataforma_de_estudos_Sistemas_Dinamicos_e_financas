/** Only an internal path is accepted as a destination after login: no open redirects. */
export function safeDestination(value: unknown): string {
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//') ? value : '/'
}
