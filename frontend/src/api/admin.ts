import request from './request'

export interface AdminUser {
  id: number
  employee_id: string
  display_name: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface UserCreate {
  employee_id: string
  display_name?: string
  password: string
  is_admin?: boolean
}

export interface UserUpdate {
  display_name?: string
  is_active?: boolean
  is_admin?: boolean
  password?: string
}

export const adminApi = {
  listUsers: () => request.get<AdminUser[]>('/admin/users'),
  createUser: (data: UserCreate) => request.post<AdminUser>('/admin/users', data),
  updateUser: (id: number, data: UserUpdate) => request.patch<AdminUser>(`/admin/users/${id}`, data),
  deleteUser: (id: number) => request.delete(`/admin/users/${id}`),
}
