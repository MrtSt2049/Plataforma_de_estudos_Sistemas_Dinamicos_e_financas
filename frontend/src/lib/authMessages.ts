interface AuthErrorLike {
  code?: string | undefined
  status?: number | undefined
}

/**
 * Turns a Supabase Auth error into a message for the user.
 *
 * Raw messages are English and may reveal more than they should, so only the known codes
 * get a specific text.
 */
export function authErrorMessage(error: AuthErrorLike): string {
  switch (error.code) {
    case 'invalid_credentials':
      return 'E-mail ou senha incorretos.'
    case 'email_not_confirmed':
      return 'Confirme seu e-mail antes de entrar. Procure a mensagem de confirmação na caixa de entrada.'
    case 'weak_password':
      return 'Essa senha é fraca. Use pelo menos 8 caracteres, misturando letras e números.'
    case 'same_password':
      return 'A nova senha precisa ser diferente da atual.'
    case 'signup_disabled':
      return 'O cadastro está desativado neste ambiente.'
    case 'over_request_rate_limit':
    case 'over_email_send_rate_limit':
      return 'Muitas tentativas em pouco tempo. Aguarde alguns minutos e tente de novo.'
    default:
      return error.status === 0 || error.status === undefined
        ? 'Não foi possível concluir. Verifique a conexão e tente de novo.'
        : 'Não foi possível concluir a operação. Tente de novo.'
  }
}
