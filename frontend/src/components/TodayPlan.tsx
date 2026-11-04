import { CheckCircle2, ChevronRight, Circle, Code2, LifeBuoy, Mic, Repeat } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plan, put } from '../lib/api'
import { useApp } from '../lib/app'
import { Badge, Card, cx, Md } from './ui'

const ICON = { problem: Code2, revision: Repeat, communication: Mic, mock: Code2, recall: LifeBuoy }

export function TodayPlan({ plan, onChange, choices = [5, 10, 15, 20, 25], title = "Today's plan" }: { plan: Plan; onChange: (p: Plan) => void; choices?: number[]; title?: string }) {
  const nav = useNavigate()
  const { bump } = useApp()
  const [busy, setBusy] = useState(false)
  const opts = Array.from(new Set([...choices, plan.minutes])).sort((a, b) => a - b)
  async function setTime(m: number) {
    setBusy(true)
    try { onChange(await put<Plan>('/api/plan/time', { minutes: m })); bump() } finally { setBusy(false) }
  }
  function open(t: Plan['tasks'][number]) {
    if (t.kind === 'problem') nav(`/app/practice/${t.ref}`)
    else if (t.kind === 'recall') nav(`/app/practice/${t.ref}?recall=1`)
    else if (t.kind === 'revision') nav(`/app/revision?card=${t.ref}`)
    else nav('/app/interview')
  }
  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-slate-100">{title}</div>
          <div className="text-xs text-slate-500">{plan.tasks.filter((t) => t.done).length}/{plan.tasks.length} done · {plan.total_minutes} of {plan.minutes} min</div>
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-line bg-ink-950/50 p-0.5">
          {opts.map((m) => (
            <button key={m} disabled={busy} onClick={() => setTime(m)} className={cx('rounded-md px-2.5 py-1 text-xs font-medium tabular-nums transition', plan.minutes === m ? 'bg-indigo-500 text-white' : 'text-slate-400 hover:text-slate-100')}>{m}m</button>
          ))}
        </div>
      </div>
      <div className="mt-3 rounded-lg border border-indigo-400/15 bg-indigo-500/[.06] px-3 py-2 text-xs text-indigo-200/90"><span className="font-medium">Rule applied:</span> {plan.rule}</div>
      <div key={plan.minutes} className={cx('fade-in mt-3 divide-y divide-line', busy && 'opacity-50')}>
        {plan.tasks.map((t, i) => {
          const I = ICON[t.kind] || Code2
          return (
            <button key={t.id} onClick={() => open(t)} className="group flex w-full items-start gap-3 py-3 text-left">
              <div className="mt-0.5">{t.done ? <CheckCircle2 size={16} className="text-emerald-400" /> : <Circle size={16} className="text-slate-600" />}</div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] tabular-nums text-slate-600">{i + 1}</span>
                  <I size={13} className={t.kind === 'problem' ? 'text-sky-300' : t.kind === 'revision' ? 'text-violet-300' : t.kind === 'recall' ? 'text-rose-300' : 'text-amber-300'} />
                  <span className={cx('text-sm font-medium', t.done ? 'text-slate-500 line-through' : 'text-slate-100')}>{t.title}</span>
                  <Badge>{t.minutes} min</Badge>
                </div>
                <Md text={t.reason} className="mt-0.5 !text-xs !text-slate-500" />
              </div>
              <ChevronRight size={15} className="mt-1 text-slate-600 transition group-hover:translate-x-0.5 group-hover:text-slate-300" />
            </button>
          )
        })}
      </div>
    </Card>
  )
}
