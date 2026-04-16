import request from './request'

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserInfo {
  id: number
  employee_id: string
  display_name: string
  is_admin: boolean
}

export const authApi = {
  login: (employee_id: string, password: string) =>
    request.post<TokenResponse>('/auth/login', { employee_id, password }),

  me: () => request.get<UserInfo>('/auth/me'),
}
