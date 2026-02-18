import { useMemo, useState } from 'react'
import { useConcierge } from '../hooks/useMessages'

export default function ConciergeWidget() {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [history, setHistory] = useState([])
  const concierge = useConcierge()

  const pending = concierge.isPending
  const lastReply = useMemo(() => concierge.data?.assistant || '', [concierge.data])

  async function submit() {
    if (!input.trim()) return
    const message = input.trim()
    setInput('')
    setHistory((prev) => [...prev, { role: 'user', content: message }])
    const out = await concierge.mutateAsync({ message, history })
    setHistory((prev) => [...prev, { role: 'assistant', content: out.assistant }])
  }

  return (
    <div className={`concierge ${open ? 'open' : ''}`}>
      {open && (
        <div className="concierge-panel panel">
          <h4>AI Concierge</h4>
          <p className="muted">Ask for intro strategy, sequence, and rationale.</p>
          <div className="concierge-log">
            {history.map((m, idx) => (
              <div key={idx} className={`chat-msg ${m.role}`}>
                <strong>{m.role === 'assistant' ? 'AI' : 'You'}:</strong> {m.content}
              </div>
            ))}
            {!history.length && <p className="muted">Try: “Give me top 3 intros for institutional custody deals.”</p>}
            {lastReply && !history.length && <p>{lastReply}</p>}
          </div>
          <div className="row">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask concierge..."
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  submit()
                }
              }}
            />
            <button className="btn primary" onClick={submit} disabled={pending}>{pending ? '...' : 'Send'}</button>
          </div>
        </div>
      )}
      <button className="btn primary concierge-toggle" onClick={() => setOpen((v) => !v)}>
        {open ? 'Close Concierge' : 'AI Concierge'}
      </button>
    </div>
  )
}
