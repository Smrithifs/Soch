export class ApiError extends Error {
  status: number
  constructor(status: number, msg: string) { super(msg); this.status = status }
}

export async function api<T = any>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(path, { ...opts, headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) } })
  if (!res.ok) {
    let msg = res.statusText
    try {
      const d = await res.json()
      msg = typeof d.detail === 'string' ? d.detail : Array.isArray(d.detail) ? d.detail.map((x: any) => x.msg).join('; ') : msg
    } catch {}
    throw new ApiError(res.status, msg)
  }
  return res.json()
}

export const post = <T = any>(p: string, body: any = {}) => api<T>(p, { method: 'POST', body: JSON.stringify(body) })
export const put = <T = any>(p: string, body: any = {}) => api<T>(p, { method: 'PUT', body: JSON.stringify(body) })

export type Profile = {
  id: number; name: string; track: 'oa' | 'interview' | 'learning'; track_label: string; level: string; language: string
  daily_minutes: number; company?: string; role?: string; days_left?: number; days_remaining?: number; event_date?: string
  questions_expected?: number; weak_topics: string[]; revise_topics: string[]; starting_topic?: string; familiar_topics: string[]
  goal?: string; months_available?: number; xp: number; streak: number; is_demo: boolean
  virtual_date?: string; time_offset_days?: number
}
export type Task = { id: number; kind: 'problem' | 'revision' | 'communication' | 'mock' | 'recall'; ref: string; title: string; minutes: number; reason: string; done: boolean }
export type Plan = { minutes: number; rule: string; tasks: Task[]; total_minutes: number }
