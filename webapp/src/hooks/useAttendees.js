import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { demoAttendees } from '../lib/demoData'

export function useAttendees(search = '', roles = []) {
  return useQuery({
    queryKey: ['attendees', search, roles.join(',')],
    queryFn: async () => {
      const q = new URLSearchParams()
      if (search) q.set('search', search)
      if (roles.length) q.set('roles', roles.join(','))
      try {
        return await api(`/api/attendees?${q.toString()}`)
      } catch (_e) {
        return { attendees: demoAttendees, count: demoAttendees.length }
      }
    }
  })
}

export function useEnrichmentList() {
  return useQuery({
    queryKey: ['enrichment-list'],
    queryFn: () => api('/api/enrichment')
  })
}

export function useRefreshEnrichment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload) =>
      api('/api/enrichment/refresh', {
        method: 'POST',
        body: JSON.stringify(payload)
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendees'] })
      queryClient.invalidateQueries({ queryKey: ['enrichment-list'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    }
  })
}
