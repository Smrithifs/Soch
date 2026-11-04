import { ChevronDown, Eye, Zap } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Badge, Card, cx, PageHeader, SourceBadge } from '../components/ui'
import { api } from '../lib/api'
import { useApp } from '../lib/app'

const AGENTS = ['All', 'Coach', 'Tutor', 'Recall Coach', 'Catch-up Planner', 'Interviewer']

export function AgentConsolePage() {
  const { version } = useApp()
  const [runs, setRuns] = useState<any[]>([])
  const [f, setF] = useState('All')
  const [open, setOpen] = useState<number | null>(null)
  useEffect(() => { api('/api/agents/runs').then(setRuns) }, [version])
  const list = runs.filter((r) => f === 'All' || r.agent === f)
  return (
    <div className="fade-in mx-auto max-w-5xl p-8">
      <PageHeader title="Agent Console" sub="Every agent decision, step by step: what it observed about you → what it decided → whether the local model or the offline rules answered." />
      <div className="mb-4 flex flex-wrap gap-1.5">{AGENTS.map((a) => <button key={a} onClick={() => setF(a)} className={cx('rounded-md border px-2.5 py-1 text-xs', f === a ? 'border-indigo-400/50 bg-indigo-500/10 text-indigo-100' : 'border-line text-slate-400')}>{a}</button>)}</div>
      {list.length === 0 && <Card className="p-8 text-center text-sm text-slate-500">No agent runs yet. Ask the tutor something, start a Recall Rescue, or build a catch-up plan.</Card>}
      <div className="relative space-y-2 before:absolute before:bottom-2 before:left-[11px] before:top-2 before:w-px before:bg-line">
        {list.map((r) => (
          <div key={r.id} className="relative pl-8">
            <div className={cx('absolute left-1.5 top-3.5 h-3 w-3 rounded-full border-2 border-ink-950', r.source === 'llm' ? 'bg-violet-400' : 'bg-slate-500')} />
            <Card className="overflow-hidden">
              <button onClick={() => setOpen(open === r.id ? null : r.id)} className="flex w-full items-center gap-2 px-4 py-2.5 text-left">
                <span className="text-sm font-medium text-slate-100">{r.agent}</span>
                <SourceBadge source={r.source} model={r.source === 'llm' ? r.model : undefined} />
                <span className="truncate text-xs text-slate-500">{r.trigger}</span>
                <span className="ml-auto shrink-0 text-[11px] tabular-nums text-slate-600">{r.latency_ms} ms · {new Date(r.at + 'Z').toLocaleTimeString()}</span>
                <ChevronDown size={13} className={cx('shrink-0 text-slate-500 transition', open === r.id && 'rotate-180')} />
              </button>
              {open === r.id && (
                <div className="grid gap-px border-t border-line bg-line md:grid-cols-2">
                  <div className="bg-ink-900 p-3"><div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-sky-300"><Eye size={11} />Observed</div><pre className="max-h-80 overflow-auto whitespace-pre-wrap font-mono text-[11px] text-slate-400">{JSON.stringify(r.observed, null, 2)}</pre></div>
                  <div className="bg-ink-900 p-3"><div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-violet-300"><Zap size={11} />Decided</div><pre className="max-h-80 overflow-auto whitespace-pre-wrap font-mono text-[11px] text-slate-300">{JSON.stringify(r.decision, null, 2)}</pre>{r.error && <div className="mt-2"><Badge tone="amber">fell back: {r.error.slice(0, 120)}</Badge></div>}</div>
                </div>
              )}
            </Card>
          </div>
        ))}
      </div>
    </div>
  )
}
