// TypeScript interfaces — mirrors backend Pydantic schemas exactly

export interface ArtifactFile {
  filename: string
  content: string
  size: number
  file_type: 'json' | 'python' | 'markdown' | 'text'
}

export interface ToolCall {
  tool: string
  input: Record<string, unknown>
  result: string
}

export interface GenerateRequest {
  description: string
  api_key?: string
}

export interface GenerateResponse {
  run_id: string
  status: 'success' | 'error'
  description: string
  artifacts: ArtifactFile[]
  tool_calls: ToolCall[]
  tool_call_count: number
  file_count: number
  duration_seconds: number
  created_at: string
}

export interface HistoryItem {
  run_id: string
  description: string
  status: string
  file_count: number
  tool_call_count: number
  created_at: string
}

export interface HistoryResponse {
  items: HistoryItem[]
  total: number
}

export interface HealthResponse {
  status: string
  version: string
  api_key_configured: boolean
}

export type GenerationStatus = 'idle' | 'loading' | 'success' | 'error'
