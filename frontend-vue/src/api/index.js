const API_BASE = import.meta.env.VITE_API_BASE || ''

function getToken() {
  return localStorage.getItem('qb_token')
}

export async function api(path, opts = {}) {
  const token = getToken()
  const headers = { ...(opts.headers || {}) }
  if (!(opts.body instanceof FormData)) headers['Content-Type'] = 'application/json'
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(API_BASE + path, { ...opts, headers })
  if (res.status === 401) {
    localStorage.removeItem('qb_token')
    localStorage.removeItem('qb_user')
    window.location.href = import.meta.env.BASE_URL + 'login'
    return
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'API Error')
  }
  return res
}

export async function apiJson(path, opts = {}) {
  const res = await api(path, opts)
  return res ? await res.json() : null
}
