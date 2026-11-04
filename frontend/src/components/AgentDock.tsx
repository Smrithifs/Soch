import { Clock, FastForward, RotateCcw } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, post } from '../lib/api'
import { useApp } from '../lib/app'
import { cx, useToast } from './ui'

/** Sidebar block: local-LLM status + demo time travel for the active student. */
export function AgentDock() {
  const { profile, bump } = useApp()
  const [st, setSt] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const toast = useToast()
  useEffect(() => {
    const load = () => api('/api/agents/status').then(setSt).catch(() => setSt(null))
    load()
    const t = setInterval(load, 20000)
    return () => clearInterval(t)
  }, [])
  async function travel(days: number) {
    setBusy(true)
    try {
      const r = days ? await post('/api/time/travel', { days }) : await post('/api/time/reset')
      toast(days ? `Jumped ${days} day${days > 1 ? 's' : ''} ahead → ${r.virtual_date}` : 'Back to real time')
      bump()
    } finally { setBusy(false) }
  }
  const off = profile?.time_offset_days || 0
  return (
    <div className="mx-3 mb-2 space-y-2">
      <div title={st?.reason || ''} className="flex items-center gap-2 rounded-md border border-line bg-white/[.02] px-2.5 py-1.5 text-[11px]">
        <span className={cx('h-1.5 w-1.5 rounded-full', st?.online ? 'bg-emerald-400 shadow-[0_0_8px] shadow-emerald-400' : 'bg-amber-400')} />
        <span className="text-slate-300">{st?.online ? 'Agents online' : 'Agents offline'}</span>
        <span className="ml-auto truncate text-slate-500">{st?.online ? st.model : 'rules fallback'}</span>
      </div>
      <div className={cx('rounded-md border px-2.5 py-2', off ? 'border-amber-400/30 bg-amber-500/[.05]' : 'border-line bg-white/[.02]')}>
        <div className="flex items-center gap-1.5 text-[11px]">
          <Clock size={11} className={off ? 'text-amber-300' : 'text-slate-500'} />
          <span className={off ? 'text-amber-200' : 'text-slate-400'}>{off ? `Simulated: ${profile?.virtual_date}` : 'Real time'}</span>
          {off > 0 && <span className="ml-auto text-amber-300/80">+{off}d</span>}
        </div>
        <div className="mt-1.5 flex gap-1">
          {[1, 3, 10].map((d) => (
            <button key={d} disabled={busy} onClick={() => travel(d)} className="flex flex-1 items-center justify-center gap-0.5 rounded bg-white/[.04] py-1 text-[10px] text-slate-300 hover:bg-white/[.09]"><FastForward size={9} />{d}d</button>
          ))}
          <button disabled={busy || !off} onClick={() => travel(0)} title="Reset to real time" className="rounded bg-white/[.04] px-1.5 text-slate-400 hover:bg-white/[.09] disabled:opacity-30"><RotateCcw size={10} /></button>
        </div>
      </div>
    </div>
  )
}
