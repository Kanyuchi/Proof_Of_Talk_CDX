import { useMemo, useState } from 'react'
import EmptyState from '../components/EmptyState'
import { useAuth } from '../context/AuthContext'
import { useChatMessages, useChatPeers, useSendMessage } from '../hooks/useMessages'

export default function MessagesPage() {
  const { user } = useAuth()
  const peers = useChatPeers()
  const [activePeer, setActivePeer] = useState('')
  const messages = useChatMessages(activePeer)
  const sendMessage = useSendMessage()
  const [input, setInput] = useState('')

  const peerList = peers.data?.peers || []
  const hasPeers = peerList.length > 0

  const activeLabel = useMemo(() => {
    const p = peerList.find((x) => x.user_id === activePeer)
    return p ? `${p.full_name} · ${p.organization}` : 'Conversation'
  }, [peerList, activePeer])

  async function send() {
    if (!activePeer || !input.trim()) return
    await sendMessage.mutateAsync({ to_user_id: activePeer, body: input.trim() })
    setInput('')
  }

  if (!user) {
    return <EmptyState title="Login required" description="Sign in on the Auth page to access private matched chat." />
  }

  return (
    <section className="grid two-cols">
      <article className="panel">
        <h2>Matched Peers</h2>
        {!hasPeers && <EmptyState title="No peers yet" description="Matched peers appear after recommendation overlap." />}
        {peerList.map((peer) => (
          <button
            key={peer.user_id}
            className={`peer-item ${activePeer === peer.user_id ? 'active' : ''}`}
            onClick={() => setActivePeer(peer.user_id)}
          >
            <strong>{peer.full_name}</strong>
            <span>{peer.title}</span>
            <span className="muted">{peer.latest_message || 'No messages yet'}</span>
          </button>
        ))}
      </article>

      <article className="panel">
        <h2>{activeLabel}</h2>
        {!activePeer ? (
          <EmptyState title="Select a peer" description="Choose a matched attendee from the left panel." />
        ) : (
          <>
            <div className="message-log">
              {(messages.data?.messages || []).map((m) => (
                <div key={m.id} className={`chat-msg ${m.from_user_id === user.id ? 'mine' : 'theirs'}`}>
                  <p>{m.body}</p>
                  <small>{m.created_at}</small>
                </div>
              ))}
            </div>
            <div className="row">
              <input
                placeholder="Type a private message"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    send()
                  }
                }}
              />
              <button className="btn primary" onClick={send}>Send</button>
            </div>
          </>
        )}
      </article>
    </section>
  )
}
