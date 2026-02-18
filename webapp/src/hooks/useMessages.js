import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export function useChatPeers() {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['chat-peers'],
    queryFn: () => api('/api/chat/peers', {}, token),
    enabled: Boolean(token),
    refetchInterval: 7000
  })
}

export function useChatMessages(peerUserId) {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['chat-messages', peerUserId],
    enabled: Boolean(token && peerUserId),
    queryFn: () => api(`/api/chat/messages/${encodeURIComponent(peerUserId)}`, {}, token),
    refetchInterval: 4000
  })
}

export function useSendMessage() {
  const queryClient = useQueryClient()
  const { token } = useAuth()
  return useMutation({
    mutationFn: ({ to_user_id, body }) =>
      api('/api/chat/messages', {
        method: 'POST',
        body: JSON.stringify({ to_user_id, body })
      }, token),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat-messages', variables.to_user_id] })
      queryClient.invalidateQueries({ queryKey: ['chat-peers'] })
    }
  })
}

export function useConcierge() {
  const { token } = useAuth()
  return useMutation({
    mutationFn: ({ message, profile_id, history }) =>
      api('/api/concierge/chat', {
        method: 'POST',
        body: JSON.stringify({ message, profile_id, history })
      }, token)
  })
}
