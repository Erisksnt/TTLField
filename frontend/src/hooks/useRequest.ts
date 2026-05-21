import { useState, useCallback } from 'react'
import toast from 'react-hot-toast'

interface UseRequestState<T> {
  data: T | null
  isLoading: boolean
  error: Error | null
}

type RequestFn<T> = () => Promise<T>

export function useRequest<T>(requestFn: RequestFn<T>) {
  const [state, setState] = useState<UseRequestState<T>>({
    data: null,
    isLoading: false,
    error: null,
  })

  const execute = useCallback(async () => {
    setState({ data: null, isLoading: true, error: null })
    try {
      const result = await requestFn()
      setState({ data: result, isLoading: false, error: null })
      return result
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Erro na requisição'
      setState({
        data: null,
        isLoading: false,
        error: new Error(errorMessage),
      })
      toast.error(errorMessage)
      throw error
    }
  }, [requestFn])

  return { ...state, execute }
}
