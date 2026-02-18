const API_BASE = import.meta.env.VITE_API_BASE || ''

export async function api(path, options = {}, token = '') {
  const headers = { ...(options.headers || {}) }
  if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  let data = {}
  try {
    data = await res.json()
  } catch (_e) {
    data = {}
  }
  if (!res.ok) {
    throw new Error(data.detail || data.error || `Request failed (${res.status})`)
  }
  return data
}
