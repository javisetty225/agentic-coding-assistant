// useGenerate — manages generation state

import { useCallback, useState } from 'react'
import { api } from '../api/client'
import type { GenerateResponse, GenerationStatus } from '../types/api'

export function useGenerate() {
  const [status, setStatus] = useState<GenerationStatus>('idle')
  const [data, setData] = useState<GenerateResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const generate = useCallback(async (description: string, apiKey?: string) => {
    setStatus('loading')
    setError(null)
    setData(null)
    try {
      const response = await api.generate({
        description,
        api_key: apiKey || undefined,
      })
      setData(response)
      setStatus('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setStatus('error')
    }
  }, [])

  const reset = useCallback(() => {
    setStatus('idle')
    setData(null)
    setError(null)
  }, [])

  return { status, data, error, generate, reset }
}
