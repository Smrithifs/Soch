import { ArrowRight, Brain, Flame, LifeBuoy, MessagesSquare, RefreshCw, Sparkles, Target, Timer, Zap } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TodayPlan } from '../components/TodayPlan'
import { Badge, Bar, Button, Card, cx, Md, PageHeader, Ring, SourceBadge, Stat } from '../components/ui'
import { api } from '../lib/api'
import { useApp } from '../lib/app'

export function DashboardPage() {
  const { version } = useApp()
  const [d, setD] = useState<any>(null)
  const load = () => api('/api/dashboard').then(setD)
  useEffect(() => { load() }, [version])
  if (!d) return <div className="p-8 text-sm text-slate-500">Loading dashboard…</div>
  const p = d.profile
  return (
    <div className="fade-in mx-auto max-w-6xl p-8">
      <CoachStrip />
      {p.track === 'oa' && <OADash d={d} onPlan={(plan: any) => setD({ ...d, plan })} />}
      {p.track === 'learning' && <LearnDash d={d} onPlan={(plan: any) => setD({ ...d, plan })} />}
      {p.track === 'interview' && <InterviewDash d={d} onPlan={(plan: any) => setD({ ...d, plan })} />}
    </div>
  )
}

function Countdown({ days, label, tone }: { days: number; label: string; tone: string }) {
  return (
    <Card className="relative overflow-hidden p-5">
      <div className={cx('absolute -right-8 -top-8 h-32 w-32 rounded-full blur-3xl', tone)} />
      <div className="text-[11px] font-medium uppercase tracking-wider text-slate-500">{label}</div>
      <div className="mt-1 flex items-baseline gap-1.5"><span className="text-5xl font-semibold tabular-nums text-slate-50">{days}</span><span className="text-sm text-slate-400">day{days === 1 ? '' : 's'} left</span></div>
      <div className="mt-3 flex gap-1">{Array.from({ length: Math.max(days, 1) }).map((_, i) => <div key={i} className={cx('h-1.5 flex-1 rounded-full', i === 0 ? 'bg-indigo-400' : 'bg-white/10')} />)}</div>
    </Card>
  )
}

function OADash({ d, onPlan }: any) {
  const p = d.profile, pr = d.progress, nav = useNavigate()
  const problems = d.plan.tasks.filter((t: any) => t.kind === 'problem')
  return (
    <>
      <PageHeader title={`${p.company} OA preparation`} sub={`${p.questions_expected} coding questions · ${p.level} · ${p.language} · ${p.daily_minutes}-minute daily target`}
        right={<Button onClick={() => nav('/app/mock-oa')}><Timer size={14} />Start timed mock OA</Button>} />
      <div className="grid gap-4 md:grid-cols-4">
        <Countdown days={p.days_left} label={`${p.company} OA`} tone="bg-sky-500/20" />
        <Card className="flex items-center gap-4 p-5"><Ring value={pr.readiness} label="OA ready" color="#38bdf8" /><div className="text-xs text-slate-400">55% planned problems solved<br />25% revision accuracy<br />20% open-mistake penalty</div></Card>
        <Stat label="Coding problems today" value={`${problems.filter((t: any) => t.done).length}/${problems.length}`} hint={`${problems.length} × 10 min timed`} accent="text-sky-300" />
        <Stat label="Revision progress" value={`${pr.revision_accuracy}%`} hint={`${pr.revision_attempts} recall attempts`} accent="text-violet-300" />
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <TodayPlan plan={d.plan} onChange={onPlan} choices={[5, 10, 15, 25]} />
        <div className="space-y-4">
          <Card className="p-5">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold"><Zap size={14} className="text-amber-300" />Timed practice recommendations</div>
            <ul className="space-y-2.5 text-sm text-slate-400">
              <li>• Set a <b className="text-slate-200">10-minute timer</b> per problem; if you're stuck at minute 6, take one hint.</li>
              <li>• Run the given examples before Submit — OAs penalise wrong submissions.</li>
              <li>• Practise both today's patterns: <b className="text-slate-200">stack matching</b> and <b className="text-slate-200">Kadane</b>.</li>
              <li>• Day {Math.max(1, 8 - (p.days_left ?? 7))}: finish with a full 2-question mock under {p.questions_expected * 25} min.</li>
            </ul>
          </Card>
          <MiniStats p={p} m={d.mistakes} />
        </div>
      </div>
    </>
  )
}

function LearnDash({ d, onPlan }: any) {
  const p = d.profile, nav = useNavigate()
  const cur = d.curriculum
  const done = cur.filter((c: any) => c.status === 'done' || c.mastery >= 60)
  const revise = d.revisions.filter((r: any) => r.last_result === 'wrong')
  const current = cur.find((c: any) => c.status === 'current')
  return (
    <>
      <PageHeader title={`${p.months_available}-month DSA roadmap`} sub={`Goal: ${p.goal} · ${p.level} · ${p.language}`} right={<Button variant="ghost" onClick={() => nav('/app/path')}>Full roadmap<ArrowRight size={14} /></Button>} />
      <Card className="mb-4 p-5">
        <div className="mb-3 flex items-center justify-between text-xs text-slate-500"><span>Roadmap · 14 topics</span><span>Current topic: <b className="text-emerald-300">{current?.topic}</b></span></div>
        <div className="flex gap-1">
          {cur.map((c: any) => (
            <div key={c.topic} title={`${c.topic} · ${c.mastery}%`} className="group flex-1">
              <div className={cx('h-2 rounded-full', c.status === 'current' ? 'bg-emerald-400 ring-2 ring-emerald-400/30' : c.status === 'done' ? 'bg-emerald-600/70' : c.status === 'revise' ? 'bg-amber-400' : c.status === 'available' ? 'bg-slate-600' : 'bg-white/[.07]')} />
              <div className={cx('mt-1.5 truncate text-[10px]', c.status === 'current' ? 'text-emerald-300' : 'text-slate-600')}>{c.topic}</div>
            </div>
          ))}
        </div>
      </Card>
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Daily learning target" value={`${p.daily_minutes} min`} hint="Change today's time in the plan" />
        <Stat label="Concepts mastered" value={done.length} hint={done.map((c: any) => c.topic).join(', ') || 'none yet'} accent="text-emerald-300" />
        <Stat label="Needs revision" value={revise.length} hint={revise.map((r: any) => r.concept).join(', ') || 'all clear'} accent={revise.length ? 'text-amber-300' : 'text-slate-50'} />
        <Stat label="Learning streak" value={<span className="flex items-center gap-1.5"><Flame size={20} className="text-orange-400" />{p.streak}</span>} hint={`${p.xp} XP total`} />
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <TodayPlan plan={d.plan} onChange={onPlan} choices={[5, 10, 15]} />
        <div className="space-y-4">
          <Card className="p-5">
            <div className="text-[11px] uppercase tracking-wider text-slate-500">Next suggested problem</div>
            <div className="mt-1 text-base font-semibold text-slate-100">{d.next_problem.title}</div>
            <p className="mt-1 text-xs text-slate-400">{d.next_problem.reason}</p>
            <Button size="sm" variant="ghost" className="mt-3" onClick={() => nav(`/app/practice/${d.next_problem.slug}`)}>Open<ArrowRight size={12} /></Button>
          </Card>
          <Card className="p-5">
            <div className="mb-3 text-sm font-semibold">Topic mastery</div>
            <div className="space-y-2.5">{cur.slice(0, 5).map((c: any) => <div key={c.topic}><div className="mb-1 flex justify-between text-xs"><span className="text-slate-300">{c.topic}</span><span className="tabular-nums text-slate-500">{c.mastery}%</span></div><Bar value={c.mastery} tone={c.status === 'revise' ? 'bg-amber-400' : 'bg-emerald-400'} /></div>)}</div>
          </Card>
        </div>
      </div>
    </>
  )
}

function InterviewDash({ d, onPlan }: any) {
  const p = d.profile, pr = d.progress, nav = useNavigate()
  const iv = d.last_interview
  const comm = iv?.scores?.Communication != null ? Math.round(iv.scores.Communication * 10) : 0
  return (
    <>
      <PageHeader title={`${p.company} internship interview`} sub={`${p.role} · revising ${(p.revise_topics || []).join(', ')} · ${p.daily_minutes} min/day`}
        right={<Button onClick={() => nav('/app/interview')}><MessagesSquare size={14} />Start mock interview</Button>} />
      <div className="grid gap-4 md:grid-cols-4">
        <Countdown days={p.days_left} label="Interview countdown" tone="bg-violet-500/25" />
        <Card className="flex items-center gap-4 p-5"><Ring value={pr.readiness} label="Technical" color="#a78bfa" /><div className="text-xs text-slate-400">Planned problems, revision accuracy, latest mock score</div></Card>
        <Card className="flex items-center gap-4 p-5"><Ring value={comm} label="Comms" color="#fbbf24" /><div className="text-xs text-slate-400">{iv ? 'From your latest mock interview' : 'Complete a mock to measure communication'}</div></Card>
        <Stat label="Revision cards" value={`${d.revisions.filter((r: any) => r.due).length} due`} hint={`${pr.revision_accuracy}% accuracy`} accent="text-violet-300" />
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <TodayPlan plan={d.plan} onChange={onPlan} choices={[10, 15, 20, 30]} title="Today's plan — revision-heavy" />
        <div className="space-y-4">
          <Card className="p-5">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold"><Target size={14} className="text-violet-300" />Three-day plan</div>
            <div className="space-y-3">
              {d.calendar.slice(0, 3).map((day: any, i: number) => (
                <div key={i} className="flex gap-3">
                  <div className={cx('flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-semibold', i === 0 ? 'bg-violet-500 text-white' : 'bg-white/[.06] text-slate-400')}>{i + 1}</div>
                  <div className="text-xs text-slate-400">{day.items.map((x: string) => <div key={x}>{x}</div>)}</div>
                </div>
              ))}
            </div>
          </Card>
          <Card className="p-5">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold"><Brain size={14} className="text-amber-300" />Revision priorities</div>
            <div className="space-y-1.5">{d.revisions.slice(0, 6).map((r: any) => <div key={r.id} className="flex items-center justify-between text-xs"><span className="text-slate-300">{r.concept}</span><Badge tone={r.last_result === 'wrong' ? 'red' : r.due ? 'violet' : 'green'}>{r.last_result === 'wrong' ? 'missed' : r.due ? 'due' : `in ${r.interval_days}d`}</Badge></div>)}</div>
          </Card>
          <MiniStats p={p} m={d.mistakes} />
        </div>
      </div>
    </>
  )
}

function MiniStats({ p, m }: any) {
  const nav = useNavigate()
  const open = m.mistakes.filter((x: any) => x.status === 'open')
  return (
    <Card className="cursor-pointer p-5 hover:border-slate-600" onClick={() => nav('/app/mistakes')}>
      <div className="flex items-center justify-between"><div className="text-sm font-semibold">Mistake DNA</div><span className="text-xs text-slate-500">{p.xp} XP · 🔥 {p.streak}</span></div>
      <div className="mt-2 text-xs text-slate-400">{open.length ? `${open.length} open: ${open.slice(0, 2).map((x: any) => x.category).join(', ')}` : 'No open mistakes.'}</div>
    </Card>
  )
}

function CoachStrip() {
  const { version } = useApp()
  const nav = useNavigate()
  const [b, setB] = useState<any>(null)
  const [mem, setMem] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  useEffect(() => { api('/api/coach').then(setB); api('/api/memory').then(setMem) }, [version])
  const forgotten = (mem?.topics || []).filter((t: any) => t.status === 'forgotten')
  return (
    <div className="mb-5 grid gap-3 lg:grid-cols-[1.6fr_1fr]">
      <Card className="flex gap-3 border-violet-400/20 bg-gradient-to-r from-violet-500/[.06] to-transparent p-4">
        <Sparkles size={16} className="mt-0.5 shrink-0 text-violet-300" />
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-violet-300">Coach · today <SourceBadge source={b?.source} /></div>
          {b ? <Md text={b.text} className="!text-[13px] !text-slate-200" /> : <div className="text-xs text-slate-500">Coach is reading your memory and plan…</div>}
        </div>
        <button title="Regenerate" disabled={busy} onClick={async () => { setBusy(true); setB(await api('/api/coach?refresh=true')); setBusy(false) }} className="self-start text-slate-500 hover:text-slate-200"><RefreshCw size={13} className={busy ? 'animate-spin' : ''} /></button>
      </Card>
      {forgotten.length > 0 ? (
        <Card className="flex items-center gap-3 border-rose-400/30 bg-rose-500/[.05] p-4 cursor-pointer" onClick={() => nav('/app/memory')}>
          <LifeBuoy className="shrink-0 text-rose-300" size={18} />
          <div className="flex-1 text-xs text-slate-300"><b className="text-rose-100">{forgotten.map((t: any) => `${t.topic} ${t.retention}%`).join(' · ')}</b><br />Slipped into the forgotten zone. Rescue before new work.</div>
          <ArrowRight size={14} className="text-rose-300" />
        </Card>
      ) : (
        <Card className="flex items-center gap-3 p-4 cursor-pointer" onClick={() => nav('/app/memory')}>
          <Brain className="shrink-0 text-emerald-300" size={18} />
          <div className="flex-1 text-xs text-slate-400">{mem?.topics?.length ? `${mem.topics.length} topics tracked · lowest ${mem.topics[0].topic} ${mem.topics[0].retention}%` : 'Memory tracking starts with your first solve.'}</div>
          <ArrowRight size={14} className="text-slate-500" />
        </Card>
      )}
    </div>
  )
}
