import request from './request'

export interface Datasource {
  id: number
  name: string
  type: string
  description: string
  config: Record<string, unknown>
  enabled: boolean
  created_at: string
}

export interface DatasourceCreate {
  name: string
  type: string
  description?: string
  config?: Record<string, unknown>
  enabled?: boolean
}

export interface DatasourceUpdate {
  name?: string
  description?: string
  config?: Record<string, unknown>
  enabled?: boolean
}

export const DATASOURCE_TYPES = ['mysql', 'postgresql', 'mssql', 'sqlite', 'http_api', 'shared']

export const datasourcesApi = {
  list: () => request.get<Datasource[]>('/datasources'),
  create: (data: DatasourceCreate) => request.post<Datasource>('/datasources', data),
  update: (id: number, data: DatasourceUpdate) => request.patch<Datasource>(`/datasources/${id}`, data),
  delete: (id: number) => request.delete(`/datasources/${id}`),
  test: (id: number) => request.post<{ success: boolean; message: string }>(`/datasources/${id}/test`),
}
