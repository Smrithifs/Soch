import { ArrowRight, Brain, LifeBuoy, Sparkles, TrendingDown } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CartesianGrid, Legend, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Badge, Button, Card, cx, Md, PageHeader, SourceBadge, useToast } from '../components/ui'
import { api, post } from '../lib/api'
import { useApp } from '../lib/app'

const COLORS = ['#818cf8', '#34d399', '#f472b6', '#fbbf24', '#38bdf8', '#a78bfa']
const TONE: Record<string, 'green' | 'amber' | 'red'> = { strong: 'green', fading: 'amber', forgotten: 'red' }

export function MemoryPage() {
  const { version, bump } = useApp()
  const [m, setM] = useState<any>(null)
  const [plan, setPlan] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()
  const toast = useToast()
  useEffect(() => { api('/api/memory').then(setM); setPlan(null) }, [version])
  if (!m) return null

  const days = [0, 1, 2, 3, 5, 7, 10, 14, 21, 30]
  const chart = days.map((d, i) => Object.fromEntries([['day', d === 0 ? 'today' : `+${d}d`], ...m.topics.map((t: any) => [t.topic, t.projection[i].retention])]))
  const weak = m.topics.filter((t: any) => t.status !== 'strong')

  async function gen() {
    setBusy(true)
    try { setPlan(await post('/api/agents/catchup')) } catch (e: any) { toast(e.message, 'err') } finally { setBusy(false) }
  }
  async function apply() { await post('/api/agents/catchup/apply', { tasks: plan.tasks }); bump(); toast("Catch-up plan applied to today"); nav('/app/dashboard') }

  return (
    <div className="fade-in mx-auto max-w-6xl p-8">
      <PageHeader title="Memory & Catch-up" sub={<>Every topic you practise decays on a forgetting curve <code className="rounded bg-white/5 px-1 text-xs">R = e^(−t/S)</code>. Each successful recall makes S (stability) bigger — reviewing <i>just as it fades</i> helps most.</>} />

      {m.days_away != null && m.days_away >= 2 && (
        <Card className="mb-4 flex flex-wrap items-center gap-3 border-amber-400/30 bg-amber-500/[.05] p-4">
          <TrendingDown className="text-amber-300" size={18} />
          <div className="flex-1 text-sm"><b className="text-amber-100">You've been away {m.days_away} days.</b> <span className="text-slate-400">{weak.length} topic{weak.length === 1 ? '' : 's'} slipped while you were gone.</span></div>
          <Button onClick={gen} disabled={busy}><Sparkles size={14} />{busy ? 'Planner thinking…' : 'Build my catch-up plan'}</Button>
        </Card>
      )}

      {m.topics.length === 0 ? (
        <Card className="p-10 text-center text-sm text-slate-400"><Brain className="mx-auto mb-3 text-slate-600" />Nothing in memory yet. Solve a problem or answer a revision card — then use the <b>time travel</b> buttons in the sidebar to watch it fade.</Card>
      ) : (
        <>
          <Card className="p-5">
            <div className="mb-1 flex items-center justify-between"><div className="text-sm font-semibold">What happens if you stop now</div><div className="text-[11px] text-slate-500">projected retention if you don't practise</div></div>
            <div className="h-72">
              <ResponsiveContainer>
                <LineChart data={chart} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <ReferenceArea y1={75} y2={100} fill="#34d399" fillOpacity={0.04} />
                  <ReferenceArea y1={45} y2={75} fill="#fbbf24" fillOpacity={0.05} />
                  <ReferenceArea y1={0} y2={45} fill="#fb7185" fillOpacity={0.06} />
                  <CartesianGrid stroke="#1c2233" vertical={false} />
                  <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
                  <Tooltip contentStyle={{ background: '#0f1320', border: '1px solid rgba(148,163,184,.15)', borderRadius: 8, fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  {m.topics.map((t: any, i: number) => <Line key={t.topic} dataKey={t.topic} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={false} type="monotone" />)}
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 flex gap-4 text-[11px] text-slate-500"><span><span className="mr-1 inline-block h-2 w-2 rounded-sm bg-emerald-400/50" />strong ≥ 75%</span><span><span className="mr-1 inline-block h-2 w-2 rounded-sm bg-amber-400/50" />fading</span><span><span className="mr-1 inline-block h-2 w-2 rounded-sm bg-rose-400/50" />forgotten &lt; 45% — you'll feel "blank"</span></div>
          </Card>

          <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {m.topics.map((t: any) => (
              <Card key={t.topic} className={cx('p-4', t.status === 'forgotten' && 'border-rose-400/30')}>
                <div className="flex items-center justify-between"><span className="text-sm font-semibold">{t.topic}</span><Badge tone={TONE[t.status]}>{t.status}</Badge></div>
                <div className="mt-2 flex items-baseline gap-2"><span className="text-3xl font-semibold tabular-nums">{t.retention}%</span><span className="text-xs text-slate-500">retention</span></div>
                <div className="mt-2 grid grid-cols-3 gap-2 text-[11px] text-slate-500">
                  <div><div className="text-slate-300">{t.days_since}d</div>since used</div>
                  <div><div className="text-slate-300">{t.stability_days}d</div>stability</div>
                  <div><div className="text-slate-300">{t.status === 'forgotten' ? 'now' : `${t.forgotten_in_days}d`}</div>until blank</div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {t.rescue_problems.map((r: any) => <Button key={r.slug} size="sm" variant={t.status === 'strong' ? 'ghost' : 'primary'} onClick={() => nav(`/app/practice/${r.slug}?recall=1`)}><LifeBuoy size={12} />Recall {r.title}</Button>)}
                  {!t.rescue_problems.length && <span className="text-[11px] text-slate-500">Recall via Smart Revision cards</span>}
                </div>
                <div className="mt-3 border-t border-line pt-2 text-[10px] text-slate-500">{t.history.map((h: any, i: number) => <span key={i} className="mr-1.5">{h.q === 'fail' ? '✗' : h.q === 'weak' ? '◐' : '●'} {h.src}</span>)}</div>
              </Card>
            ))}
          </div>
          {!plan && (!m.days_away || m.days_away < 2) && <div className="mt-4 text-right"><Button variant="ghost" onClick={gen} disabled={busy}><Sparkles size={14} />{busy ? 'Planner thinking…' : 'Ask the Catch-up Planner anyway'}</Button></div>}
        </>
      )}

      {plan && (
        <Card className="fade-in mt-4 border-violet-400/30 p-5">
          <div className="flex items-center gap-2"><Sparkles size={15} className="text-violet-300" /><span className="text-sm font-semibold">Catch-up plan</span><SourceBadge source={plan.source} /><span className="ml-auto text-xs text-slate-500">{plan.total_minutes} / {plan.analysis.minutes_available} min</span></div>
          <Md text={plan.message} className="mt-2" />
          <div className="mt-3 divide-y divide-line">
            {plan.tasks.map((t: any, i: number) => (
              <div key={t.id} className="flex gap-3 py-2.5">
                <span className="w-4 text-xs tabular-nums text-slate-600">{i + 1}</span>
                <div className="flex-1"><div className="flex items-center gap-2 text-sm"><span className="text-slate-100">{t.title}</span><Badge tone={t.kind === 'recall' ? 'red' : t.kind === 'revision' ? 'violet' : 'blue'}>{t.kind}</Badge><Badge>{t.minutes} min</Badge></div><div className="mt-0.5 text-xs text-slate-500">{t.reason}</div></div>
              </div>
            ))}
          </div>
          <div className="mt-3 flex gap-2"><Button onClick={apply}>Use as today's plan<ArrowRight size={14} /></Button><Button variant="subtle" onClick={() => nav('/app/agents')}>See how it decided</Button></div>
        </Card>
      )}
    </div>
  )
}
