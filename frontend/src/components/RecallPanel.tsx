import { LifeBuoy, Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api, post } from '../lib/api'
import { useApp } from '../lib/app'
import { Button, cx, Md, SourceBadge } from './ui'

/** Recall Rescue: retrieval-practice ladder for "I solved this before but I'm blank now". */
export function RecallPanel({ slug, autoStart, onStart }: { slug: string; autoStart?: boolean; onStart?: () => void }) {
  const [s, setS] = useState<any>(null)
  const [a, setA] = useState('')
  const [busy, setBusy] = useState(false)
  const { bump } = useApp()
  const end = useRef<HTMLDivElement>(null)
  const started = useRef(false)
  useEffect(() => {
    if (started.current) return
    started.current = true
    api(`/api/recall/active?slug=${slug}`).then((x) => {
      if (x && x.status === 'active') setS(x)
      else if (autoStart) start()
      else setS(x)
    })
  }, [slug])
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [s?.messages?.length])
  async function start() { setBusy(true); try { setS(await post('/api/recall/start', { slug })); onStart?.() } finally { setBusy(false) } }
  async function send(e?: React.FormEvent) {
    e?.preventDefault(); if (!a.trim()) return
    setBusy(true)
    try { const r = await post(`/api/recall/${s.id}/reply`, { answer: a }); setS(r); setA(''); if (r.status === 'complete') bump() } finally { setBusy(false) }
  }
  if (!s || s.status !== 'active' && !s.messages?.length) return (
    <div className="p-4 text-sm text-slate-400">
      <LifeBuoy className="mb-2 text-rose-300" size={20} />
      <div className="font-medium text-slate-200">Solved this before but now you're blank?</div>
      <p className="mt-1 text-xs">That's the forgetting curve, not a skill problem. The Recall Coach won't show you the answer — it pulls it back out of your memory in 6 small steps, then checks you can rebuild it with a real submission.</p>
      <Button className="mt-3" size="sm" onClick={start} disabled={busy}><LifeBuoy size={12} />Start Recall Rescue</Button>
    </div>
  )
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex shrink-0 gap-1 border-b border-line px-3 py-2">
        {s.steps.map((st: string, i: number) => <div key={st} title={st} className="flex-1"><div className={cx('h-1 rounded-full', i < s.stage ? 'bg-emerald-400' : i === s.stage && s.status === 'active' ? 'bg-rose-400' : 'bg-white/10')} /><div className={cx('mt-1 truncate text-[9px]', i === s.stage ? 'text-slate-200' : 'text-slate-600')}>{st}</div></div>)}
      </div>
      <div className="min-h-0 flex-1 space-y-2.5 overflow-y-auto p-3">
        {s.messages.map((m: any, i: number) => m.role === 'user'
          ? <div key={i} className="ml-8 rounded-lg bg-rose-500/10 px-3 py-2 text-sm text-rose-50">{m.content}</div>
          : <div key={i} className={cx('rounded-lg border p-3', m.passed === true ? 'border-emerald-400/20 bg-emerald-500/[.04]' : m.passed === false ? 'border-amber-400/20 bg-amber-500/[.04]' : 'border-line bg-ink-850')}>
              <Md text={m.content} />{m.source && <div className="mt-1.5"><SourceBadge source={m.source === 'rules' ? 'fallback' : m.source} /></div>}
            </div>)}
        <div ref={end} />
      </div>
      {s.status === 'active' ? (
        <form onSubmit={send} className="flex shrink-0 gap-2 border-t border-line p-2.5">
          <input value={a} onChange={(e) => setA(e.target.value)} placeholder={s.stage === 5 ? "Submit in the editor, then type 'done'" : 'Answer from memory — rough is fine'} className="flex-1 rounded-md border border-line bg-ink-950 px-2.5 py-1.5 text-sm outline-none focus:border-rose-400/50" />
          <Button size="sm" disabled={busy}><Send size={12} /></Button>
        </form>
      ) : <div className="shrink-0 border-t border-line p-2.5"><Button size="sm" variant="ghost" onClick={start}>Run another recall</Button></div>}
    </div>
  )
}
