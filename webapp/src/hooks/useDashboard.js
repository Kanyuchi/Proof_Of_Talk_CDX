import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { demoOverview, demoPairs } from '../lib/demoData'
import { useAuth } from '../context/AuthContext'

export function useDashboardData() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      try {
        return await api('/api/dashboard')
      } catch (_e) {
        return {
          overview: demoOverview,
          top_intro_pairs: demoPairs,
          top_non_obvious_pairs: [],
          per_profile: {}
        }
      }
    }
  })
}

export function useSegments() {
  return useQuery({
    queryKey: ['dashboard-segments'],
    queryFn: async () => {
      try {
        return await api('/api/dashboard/segments')
      } catch (_e) {
        return { roles: {}, top_interest_tags: [] }
      }
    }
  })
}

export function useDrilldown(fromId, toId) {
  return useQuery({
    queryKey: ['drilldown', fromId, toId],
    enabled: Boolean(fromId && toId),
    queryFn: () => api(`/api/dashboard/drilldown?from_id=${encodeURIComponent(fromId)}&to_id=${encodeURIComponent(toId)}`)
  })
}

export function useSaveAction() {
  const queryClient = useQueryClient()
  const { token } = useAuth()
  return useMutation({
    mutationFn: async (payload) => {
      try {
        return await api('/api/admin/actions', {
          method: 'POST',
          body: JSON.stringify(payload)
        }, token)
      } catch (_err) {
        return await api('/api/actions', {
          method: 'POST',
          body: JSON.stringify(payload)
        })
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['drilldown'] })
    }
  })
}
