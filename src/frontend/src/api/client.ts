// Typed API client — all calls to the FastAPI backend

import type {
  GenerateRequest,
  GenerateResponse,
  HealthResponse,
  HistoryResponse,
} from '../types/api'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((err as { detail: string }).detail ?? 'Request failed')
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () =>
    request<HealthResponse>('/health'),

  generate: (body: GenerateRequest) =>
    request<GenerateResponse>('/api/v1/generate', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  history: () =>
    request<HistoryResponse>('/api/v1/history'),

  downloadUrl: (runId: string, filename: string) =>
    `${BASE_URL}/api/v1/generate/${runId}/download/${filename}`,
}
