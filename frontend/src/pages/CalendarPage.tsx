import { ChevronLeft, ChevronRight, Code2, LifeBuoy, Mic, Repeat, Star } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge, Button, Card, cx, Md, PageHeader } from '../components/ui'
import { api } from '../lib/api'
import { useApp } from '../lib/app'

const ICON: any = { problem: Code2, revision: Repeat, recall: LifeBuoy, communication: Mic, event: Star }
const TONE: any = { problem: 'text-sky-300', revision: 'text-violet-300', recall: 'text-rose-300', communication: 'text-amber-300', event: 'text-amber-300' }

export function CalendarPage() {
  const { profile, version } = useApp()
  const nav = useNavigate()
  const vd = profile?.virtual_date ? new Date(profile.virtual_date + 'T00:00') : new Date()
  const [ym, setYm] = useState({ y: vd.getFullYear(), m: vd.getMonth() + 1 })
  const [month, setMonth] = useState<any>(null)
  const [sel, setSel] = useState<string | null>(null)
  const [day, setDay] = useState<any>(null)
  useEffect(() => { api(`/api/calendar/month?year=${ym.y}&month=${ym.m}`).then((m) => { setMonth(m); if (!sel) setSel(m.today) }) }, [ym, version])
  useEffect(() => { if (sel) { setDay(null); api(`/api/calendar/day?date=${sel}`).then(setDay) } }, [sel, version])
  if (!month) return null
  const lead = (new Date(ym.y, ym.m - 1, 1).getDay() + 6) % 7 // Monday-first
  const cells = [...Array(lead).fill(null), ...month.days]
  const shift = (d: number) => setYm(({ y, m }) => { const t = new Date(y, m - 1 + d, 1); return { y: t.getFullYear(), m: t.getMonth() + 1 } })
  const title = new Date(ym.y, ym.m - 1, 1).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })

  return (
    <div className="fade-in mx-auto max-w-6xl p-8">
      <PageHeader title="Calendar" sub={profile?.event_date ? `Counting down to your ${profile.track === 'oa' ? 'OA' : 'interview'} on ${new Date(profile.event_date + 'T00:00').toDateString()}. Click any day to see exactly what you'll do.` : 'Click any day to see its full plan.'} />
      <div className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <Card className="p-4">
          <div className="mb-3 flex items-center justify-between">
            <button onClick={() => shift(-1)} className="rounded-md p-1.5 text-slate-400 hover:bg-white/5"><ChevronLeft size={16} /></button>
            <div className="text-sm font-semibold">{title}</div>
            <button onClick={() => shift(1)} className="rounded-md p-1.5 text-slate-400 hover:bg-white/5"><ChevronRight size={16} /></button>
          </div>
          <div className="grid grid-cols-7 gap-1 text-center text-[10px] uppercase tracking-wider text-slate-500">{['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => <div key={d} className="py-1">{d}</div>)}</div>
          <div className="grid grid-cols-7 gap-1">
            {cells.map((c, i) => c === null ? <div key={'e' + i} /> : (
              <button key={c.date} onClick={() => setSel(c.date)} className={cx('flex h-20 flex-col rounded-lg border p-1.5 text-left transition',
                sel === c.date ? 'border-indigo-400/70 bg-indigo-500/10' : c.tag === 'event' ? 'border-amber-400/40 bg-amber-500/[.06]' : c.tag === 'today' ? 'border-sky-400/40' : 'border-line hover:border-slate-600',
                c.tag === 'past' && 'opacity-50')}>
                <span className={cx('text-xs tabular-nums', c.tag === 'today' ? 'flex h-5 w-5 items-center justify-center rounded-full bg-sky-500 font-semibold text-white' : 'text-slate-300')}>{+c.date.slice(8)}</span>
                {c.tag === 'event' && <span className="mt-auto truncate text-[10px] font-medium text-amber-300">★ {profile?.track === 'oa' ? 'OA' : 'Interview'}</span>}
                {c.tag === 'plan' && c.focus && <span className="mt-auto truncate text-[10px] text-slate-500">{c.focus}</span>}
                {c.tag === 'today' && <span className="mt-auto text-[10px] text-sky-300">today</span>}
                {c.activity > 0 && <span className="mt-auto text-[10px] text-emerald-400">● {c.activity} submit{c.activity > 1 ? 's' : ''}</span>}
              </button>
            ))}
          </div>
        </Card>
        <Card className="p-5">
          {!day ? <div className="text-sm text-slate-500">Loading day…</div> : (
            <div className="fade-in">
              <div className="text-[11px] uppercase tracking-wider text-slate-500">{new Date(day.date + 'T00:00').toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })}</div>
              <div className="mt-1 flex items-center gap-2 text-lg font-semibold">{day.title}{day.kind === 'future' && <Badge>projected</Badge>}{day.kind === 'today' && <Badge tone="blue">live plan</Badge>}</div>
              {day.total_minutes != null && <div className="text-xs text-slate-500">{day.tasks.length} activities · {day.total_minutes} min</div>}
              {day.rule && <div className="mt-2 rounded-md border border-indigo-400/15 bg-indigo-500/[.06] px-2.5 py-1.5 text-[11px] text-indigo-200/90">{day.rule}</div>}
              <div className="mt-3 space-y-2">
                {day.tasks.length === 0 && <div className="text-sm text-slate-500">Nothing here.</div>}
                {day.tasks.map((t: any, i: number) => { const I = ICON[t.kind] || Code2; return (
                  <div key={i} className="flex gap-3 rounded-lg border border-line bg-white/[.02] p-3">
                    <I size={15} className={cx('mt-0.5 shrink-0', TONE[t.kind])} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 text-sm text-slate-100">{t.title}{t.minutes != null && <Badge>{t.minutes} min</Badge>}{t.done && <Badge tone="green">done</Badge>}</div>
                      {t.detail && <Md text={t.detail} className="mt-0.5 !text-xs !text-slate-500" />}
                    </div>
                    {t.kind === 'problem' && t.ref && <button onClick={() => nav(`/app/practice/${t.ref}`)} className="self-center text-xs text-sky-300 hover:underline">Open</button>}
                    {t.kind === 'revision' && t.ref && <button onClick={() => nav(`/app/revision?card=${t.ref}`)} className="self-center text-xs text-violet-300 hover:underline">Open</button>}
                  </div>) })}
              </div>
              {day.note && <p className="mt-3 text-xs text-slate-500">{day.note}</p>}
              {day.kind === 'today' && <Button size="sm" className="mt-3" onClick={() => nav('/app/dashboard')}>Start today</Button>}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
