import { ArrowLeft, ArrowRight, BookOpen, Briefcase, Check, Clock, Code2, Sparkles, Timer } from 'lucide-react'
import { ReactNode, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, cx, inputClass, useToast } from '../components/ui'
import { post } from '../lib/api'
import { useApp } from '../lib/app'

const TRACKS = [
  { id: 'oa', title: 'Online Assessment', sub: 'Timed coding rounds. Speed, patterns, accuracy.', icon: Timer, tone: 'from-sky-500/20' },
  { id: 'interview', title: 'Technical Interviews', sub: 'Explain, optimise, communicate under pressure.', icon: Briefcase, tone: 'from-violet-500/20' },
  { id: 'learning', title: 'DSA Learning', sub: 'A structured path from fundamentals to DP.', icon: BookOpen, tone: 'from-emerald-500/20' },
] as const
const TOPICS = ['Arrays', 'Strings', 'Hashing', 'Two Pointers', 'Sliding Window', 'Linked Lists', 'Stacks', 'Binary Search', 'Recursion', 'Trees', 'Graphs', 'Dynamic Programming']
const LEVELS = ['Beginner', 'Intermediate', 'Advanced']
const LANGS = ['Java', 'Python']
const MINUTES = [5, 10, 15, 20, 25, 30, 45, 60]

const PRESETS: Record<string, any> = {
  Smrithi: { name: 'Smrithi', track: 'oa', company: 'Zscaler', days_remaining: 7, questions_expected: 2, level: 'Beginner', language: 'Java', daily_minutes: 25, weak_topics: [] },
  Dhanya: { name: 'Dhanya', track: 'learning', goal: 'Prepare for DSA next year', starting_topic: 'Hashing', months_available: 6, level: 'Beginner', language: 'Java', daily_minutes: 15, familiar_topics: ['Arrays'] },
  Vismaya: { name: 'Vismaya', track: 'interview', company: 'Microsoft', role: 'Software Engineering Internship', days_remaining: 3, level: 'Beginner', language: 'Java', revise_topics: ['Arrays', 'Hashing', 'Stacks'], daily_minutes: 20 },
}

function Choice({ options, value, onChange, multi, suffix = '' }: { options: (string | number)[]; value: any; onChange: (v: any) => void; multi?: boolean; suffix?: string }) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => {
        const on = multi ? (value || []).includes(o) : value === o
        return (
          <button type="button" key={o} onClick={() => onChange(multi ? (on ? value.filter((x: any) => x !== o) : [...(value || []), o]) : o)}
            className={cx('rounded-lg border px-3 py-1.5 text-sm transition', on ? 'border-indigo-400/60 bg-indigo-500/15 text-indigo-100' : 'border-line bg-white/[.02] text-slate-400 hover:border-slate-600 hover:text-slate-200')}>
            {on && multi && <Check size={12} className="-ml-0.5 mr-1 inline" />}{o}{suffix}
          </button>
        )
      })}
    </div>
  )
}

function Q({ label, children }: { label: string; children: ReactNode }) {
  return <div className="space-y-2"><div className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</div>{children}</div>
}

export function SignupPage() {
  const [f, setF] = useState<any>({ name: '', track: '', level: 'Beginner', language: 'Java', daily_minutes: 20, weak_topics: [], revise_topics: [], familiar_topics: [] })
  const [step, setStep] = useState(0)
  const [busy, setBusy] = useState(false)
  const { profiles, refresh } = useApp()
  const nav = useNavigate()
  const toast = useToast()
  const set = (k: string) => (v: any) => setF((x: any) => ({ ...x, [k]: v }))

  const steps: { title: string; body: ReactNode; ok: boolean }[] = []
  if (f.track === 'oa') steps.push(
    { title: 'Your assessment', ok: !!f.company && f.days_remaining > 0 && !!f.questions_expected, body: <>
      <Q label="Target company"><input className={inputClass} placeholder="e.g. Zscaler" value={f.company || ''} onChange={(e) => set('company')(e.target.value)} /></Q>
      <Q label="Days remaining"><Choice options={[3, 5, 7, 10, 14, 21]} suffix=" days" value={f.days_remaining} onChange={set('days_remaining')} /></Q>
      <Q label="Coding questions expected"><Choice options={[1, 2, 3, 4]} value={f.questions_expected} onChange={set('questions_expected')} /></Q></> },
    { title: 'Your level', ok: true, body: <><Q label="DSA level"><Choice options={LEVELS} value={f.level} onChange={set('level')} /></Q><Q label="Programming language"><Choice options={LANGS} value={f.language} onChange={set('language')} /></Q></> },
    { title: 'Your time & gaps', ok: true, body: <><Q label="Daily available time"><Choice options={MINUTES} suffix=" min" value={f.daily_minutes} onChange={set('daily_minutes')} /></Q><Q label="Weak topics (optional)"><Choice multi options={TOPICS} value={f.weak_topics} onChange={set('weak_topics')} /></Q></> },
  )
  if (f.track === 'interview') steps.push(
    { title: 'Your interview', ok: !!f.company && !!f.role && f.days_remaining >= 0 && f.days_remaining !== undefined, body: <>
      <Q label="Target company"><input className={inputClass} placeholder="e.g. Microsoft" value={f.company || ''} onChange={(e) => set('company')(e.target.value)} /></Q>
      <Q label="Target role"><input className={inputClass} placeholder="e.g. Software Engineering Internship" value={f.role || ''} onChange={(e) => set('role')(e.target.value)} /></Q>
      <Q label="Interview in (days)"><Choice options={[1, 2, 3, 5, 7, 14, 30]} suffix=" days" value={f.days_remaining} onChange={set('days_remaining')} /></Q></> },
    { title: 'Your level', ok: true, body: <><Q label="DSA level"><Choice options={LEVELS} value={f.level} onChange={set('level')} /></Q><Q label="Programming language"><Choice options={LANGS} value={f.language} onChange={set('language')} /></Q></> },
    { title: 'What to revise', ok: f.revise_topics.length > 0, body: <><Q label="Topics to revise"><Choice multi options={TOPICS} value={f.revise_topics} onChange={set('revise_topics')} /></Q><Q label="Daily available time"><Choice options={MINUTES} suffix=" min" value={f.daily_minutes} onChange={set('daily_minutes')} /></Q></> },
  )
  if (f.track === 'learning') steps.push(
    { title: 'Where you are', ok: !!f.starting_topic, body: <><Q label="DSA level"><Choice options={LEVELS} value={f.level} onChange={set('level')} /></Q><Q label="Starting topic"><Choice options={TOPICS} value={f.starting_topic} onChange={set('starting_topic')} /></Q><Q label="Topics already familiar with"><Choice multi options={TOPICS} value={f.familiar_topics} onChange={set('familiar_topics')} /></Q></> },
    { title: 'Your goal', ok: !!f.goal && !!f.months_available, body: <><Q label="Learning goal"><input className={inputClass} placeholder="e.g. Prepare for DSA next year" value={f.goal || ''} onChange={(e) => set('goal')(e.target.value)} /></Q><Q label="Months available"><Choice options={[1, 2, 3, 6, 9, 12]} suffix=" months" value={f.months_available} onChange={set('months_available')} /></Q></> },
    { title: 'Your routine', ok: true, body: <><Q label="Programming language"><Choice options={LANGS} value={f.language} onChange={set('language')} /></Q><Q label="Daily available time"><Choice options={MINUTES} suffix=" min" value={f.daily_minutes} onChange={set('daily_minutes')} /></Q></> },
  )
  const total = steps.length + 1
  const cur = step === 0 ? null : steps[step - 1]

  async function submit() {
    setBusy(true)
    try {
      await post('/api/profiles', f)
      await refresh()
      toast(`Personalized plan generated for ${f.name}`)
      nav('/app/dashboard')
    } catch (e: any) { toast(e.message, 'err') } finally { setBusy(false) }
  }
  async function resume(id: number) { await post('/api/profiles/active', { user_id: id }); await refresh(); nav('/app/dashboard') }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(60rem_30rem_at_50%_-10%,rgba(99,102,241,.18),transparent)]" />
      <div className="relative mx-auto grid max-w-6xl gap-10 px-6 py-12 lg:grid-cols-[1.1fr_1fr]">
        <div className="pt-6">
          <div className="mb-10 flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-400 to-violet-500 text-sm font-bold text-white">S</div>
            <span className="font-semibold tracking-tight">SOCH</span>
          </div>
          <h1 className="text-4xl font-semibold leading-[1.1] tracking-tight text-slate-50 md:text-5xl">Your DSA journey.<br /><span className="text-indigo-300">Your rules.</span></h1>
          <p className="mt-4 max-w-md text-slate-400">Prepare smarter with a learning path that adapts to your goals.</p>
          <div className="mt-10 grid max-w-md gap-3 text-sm text-slate-400">
            {[[Sparkles, 'Deterministic personalization — the same profile always gets the same, explainable plan.'], [Code2, 'Real Java execution. Every verdict comes from an actual compiler and test run.'], [Clock, 'Plans recalculate the moment your available time changes.']].map(([I, t]: any) => (
              <div key={t} className="flex gap-3"><I size={16} className="mt-0.5 shrink-0 text-indigo-300" />{t}</div>
            ))}
          </div>
          {profiles.length > 0 && (
            <div className="mt-10 max-w-md">
              <div className="mb-2 text-xs uppercase tracking-wider text-slate-500">Continue as</div>
              <div className="flex flex-wrap gap-2">
                {profiles.map((p) => <button key={p.id} onClick={() => resume(p.id)} className="rounded-lg border border-line bg-white/[.03] px-3 py-1.5 text-sm hover:bg-white/[.07]">{p.name} <span className="text-slate-500">· {p.track_label}</span></button>)}
              </div>
            </div>
          )}
        </div>

        <Card className="fade-in self-start p-6 shadow-2xl shadow-black/40">
          <div className="mb-5 flex items-center justify-between">
            <div className="text-xs text-slate-500">Step {step + 1} of {f.track ? total : '…'}</div>
            <div className="flex gap-1">{Array.from({ length: f.track ? total : 4 }).map((_, i) => <div key={i} className={cx('h-1 w-6 rounded-full transition', i <= step ? 'bg-indigo-400' : 'bg-white/10')} />)}</div>
          </div>
          {step === 0 ? (
            <div key="s0" className="fade-in space-y-5">
              <h2 className="text-lg font-semibold">Let's set up your plan</h2>
              <Q label="Your name"><input autoFocus className={inputClass} placeholder="First name" value={f.name} onChange={(e) => set('name')(e.target.value)} /></Q>
              <Q label="What are you preparing for?">
                <div className="grid gap-2">
                  {TRACKS.map((t) => (
                    <button key={t.id} onClick={() => set('track')(t.id)} className={cx('flex items-center gap-3 rounded-xl border bg-gradient-to-r to-transparent p-3.5 text-left transition', t.tone, f.track === t.id ? 'border-indigo-400/60 ring-2 ring-indigo-500/20' : 'border-line from-transparent hover:border-slate-600')}>
                      <t.icon size={18} className="text-slate-200" />
                      <div className="flex-1"><div className="text-sm font-medium text-slate-100">{t.title}</div><div className="text-xs text-slate-400">{t.sub}</div></div>
                      {f.track === t.id && <Check size={16} className="text-indigo-300" />}
                    </button>
                  ))}
                </div>
              </Q>
              <div className="border-t border-line pt-4">
                <div className="mb-2 text-[11px] uppercase tracking-wider text-slate-500">Demo presets</div>
                <div className="flex gap-2">{Object.keys(PRESETS).map((n) => <Button key={n} size="sm" variant="ghost" onClick={() => setF({ weak_topics: [], revise_topics: [], familiar_topics: [], ...PRESETS[n] })}>{n}</Button>)}</div>
              </div>
            </div>
          ) : step <= steps.length ? (
            <div key={step} className="fade-in space-y-5"><h2 className="text-lg font-semibold">{cur!.title}</h2>{cur!.body}</div>
          ) : null}
          <div className="mt-7 flex justify-between">
            <Button variant="subtle" disabled={step === 0} onClick={() => setStep(step - 1)}><ArrowLeft size={14} />Back</Button>
            {step < steps.length || step === 0 ? (
              <Button disabled={step === 0 ? !f.name.trim() || !f.track : !cur?.ok} onClick={() => setStep(step + 1)}>Continue<ArrowRight size={14} /></Button>
            ) : (
              <Button disabled={busy || !cur?.ok} onClick={submit}>{busy ? 'Generating plan…' : 'Generate my plan'}<Sparkles size={14} /></Button>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
